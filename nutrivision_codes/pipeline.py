"""
pipeline.py  —  Core logic for Food Weight & Nutrition Pipeline.

Key design rules
─────────────────
• save_dir is ALWAYS passed in by the caller — never read from config.
• Matplotlib OO API (Figure / FigureCanvasAgg) — not pyplot (not thread-safe).
• PCA images go to the LLM only — never shown to users.
• Users see: one combined annotated image + a clean nutrition table.
• run_pipeline_steps() is a generator that yields progress after each stage.
• Density is looked up from food_density.json ONCE and hard-enforced after
  LLM parse — the model only does geometry, not density.

"""

import base64
import json
import os
import re

import matplotlib
import numpy as np

matplotlib.use("Agg")
import torch
from config import (COIN_CONF_THRESH, COIN_DIAMETER_CM, CONF_THRESH,  # [FIX 1]
                    CONT_THRESH, CONVNEXT_CONF_THRESH, DENSITY_PATH,
                    IOU_THRESH, NUTRIENT_COLS, NUTRITION_PATH, OLLAMA_API_KEY,
                    OLLAMA_BASE_URL, OLLAMA_MODEL, PROMPT_1, PROMPT_2,
                    PROMPT_3, PROMPT_COIN)
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Ellipse
from models import get_classifier, get_device, get_sam
from PIL import Image
from pydantic import BaseModel, Field
from sklearn.decomposition import PCA as skPCA

# ════════════════════════════════════════════════════════════════════════════
# Custom exception
# ════════════════════════════════════════════════════════════════════════════

class CoinNotFoundError(Exception):
    """Raised when no coin is detected in the image."""
    pass


# ════════════════════════════════════════════════════════════════════════════
# Nutrition DB
# ════════════════════════════════════════════════════════════════════════════

with open(NUTRITION_PATH) as _f:
    _raw_db = json.load(_f)
NUTRITION_DB: dict = _raw_db["nutrition"]


# ════════════════════════════════════════════════════════════════════════════
# Density DB  — loaded once at import, never mutated
# ════════════════════════════════════════════════════════════════════════════

with open(DENSITY_PATH) as _f:             # [FIX 1]
    _DENSITY_DB: dict = json.load(_f)["density"]


def _get_density(food_class: str) -> tuple[float, str]:
    key = food_class.strip().lower()
    entry = _DENSITY_DB.get(key)
    if entry is None:
        raise KeyError(
            f"[density] '{key}' not found in food_density.json. "
            f"Add it before running inference."
        )
    return float(entry["density_g_per_cm3"]), "food_density.json"

# ════════════════════════════════════════════════════════════════════════════
# Minimal Detections container
# ════════════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════════
# Image resize helper  (keeps uploaded photos from OOM-ing SAM3)
# ════════════════════════════════════════════════════════════════════════════

_SAM_INPUT_SIZE = 1008   # standard square input for SAM3

def _resize_for_sam(image_pil: Image.Image) -> Image.Image:
    """
    Resize every image to exactly 1008×1008 pixels — SAM3's standard
    square input size — regardless of original dimensions or aspect ratio.
    Small images are upscaled, large images are downscaled.
    """
    if image_pil.size == (_SAM_INPUT_SIZE, _SAM_INPUT_SIZE):
        return image_pil
    print(f"  [resize] {image_pil.size} → {_SAM_INPUT_SIZE}×{_SAM_INPUT_SIZE}")
    return image_pil.resize(
        (_SAM_INPUT_SIZE, _SAM_INPUT_SIZE),
        Image.LANCZOS,
    )



class Detections:
    """Minimal drop-in: .xyxy  .confidence  .mask  len()  .filter()"""
    def __init__(self, xyxy, confidence, mask):
        self.xyxy       = np.asarray(xyxy,       dtype=np.float32)
        self.confidence = np.asarray(confidence, dtype=np.float32)
        self.mask       = np.asarray(mask,       dtype=bool)

    def __len__(self):
        return len(self.confidence)

    def filter(self, keep: np.ndarray):
        return Detections(self.xyxy[keep], self.confidence[keep], self.mask[keep])


def _empty_dets():
    return Detections(
        np.zeros((0, 4), dtype=np.float32),
        np.zeros((0,),   dtype=np.float32),
        np.zeros((0, 1, 1), dtype=bool),
    )


# ════════════════════════════════════════════════════════════════════════════
# SAM3 helpers
# ════════════════════════════════════════════════════════════════════════════

def _results_to_dets(results) -> Detections:
    if len(results["scores"]) == 0:
        return _empty_dets()
    masks  = np.stack([m.cpu().numpy().astype(bool) for m in results["masks"]], axis=0)
    boxes  = results["boxes"].cpu().numpy().astype(np.float32)
    scores = results["scores"].cpu().numpy().astype(np.float32)
    return Detections(boxes, scores, masks)


def get_dets(image: Image.Image, prompt: str,
             conf_thresh: float = CONF_THRESH) -> Detections:
    """Run SAM3 with a text prompt on a PIL image."""
    sam_model, sam_processor = get_sam()
    device = get_device()
    inputs = sam_processor(
        images=image, text=prompt, return_tensors="pt"
    ).to(device)
    with torch.no_grad():
        outputs = sam_model(**inputs)
    # [FIX 13] Use direct key access — .get() silently returns None on a miss,
    # which causes .tolist() to raise AttributeError with no useful traceback.
    results = sam_processor.post_process_instance_segmentation(
        outputs,
        threshold=0.0,
        mask_threshold=0.5,
        target_sizes=inputs["original_sizes"].tolist()
    )[0]
    dets = _results_to_dets(results)
    if len(dets) == 0:
        return dets
    return dets.filter(dets.confidence >= conf_thresh)


def _mask_iou(m1, m2):
    inter = np.logical_and(m1, m2).sum()
    union = np.logical_or(m1,  m2).sum()
    return float(inter / union) if union > 0 else 0.0


def _mask_containment(m_small, m_large):
    inter = np.logical_and(m_small, m_large).sum()
    area  = m_small.sum()
    return float(inter / area) if area > 0 else 0.0


def merge_detections(det_p1, det_p2, det_p3,
                     prompt_labels,
                     iou_threshold=0.30,
                     containment_threshold=0.25):
    masks, xyxys, confs, tags = [], [], [], []
    SPECIFIC_TAGS  = {0, 1}
    FOOD_ONLY_TAGS = {2}
    tag_name = {i: lbl for i, lbl in enumerate(prompt_labels)}

    for src_idx, dets in enumerate([det_p1, det_p2, det_p3]):
        if dets is None or len(dets) == 0:
            continue
        for i in range(len(dets)):
            masks.append(dets.mask[i])
            xyxys.append(dets.xyxy[i])
            confs.append(float(dets.confidence[i]))
            tags.append(src_idx)

    n = len(masks)
    if n == 0:
        return _empty_dets(), []

    iou_mat = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(i + 1, n):
            v = _mask_iou(masks[i], masks[j])
            iou_mat[i, j] = iou_mat[j, i] = v

    visited = [False] * n
    groups  = []
    for start in range(n):
        if visited[start]:
            continue
        group, queue = [], [start]
        visited[start] = True
        while queue:
            cur = queue.pop()
            group.append(cur)
            for nb in range(n):
                if not visited[nb] and iou_mat[cur, nb] >= iou_threshold:
                    visited[nb] = True
                    queue.append(nb)
        groups.append(group)

    keep_indices = []
    for group in groups:
        containers = [idx for idx in group if tags[idx] in SPECIFIC_TAGS]
        food_only  = [idx for idx in group if tags[idx] in FOOD_ONLY_TAGS]
        if containers:
            keep_indices.append(max(containers, key=lambda idx: confs[idx]))
        elif food_only:
            keep_indices.append(max(food_only, key=lambda idx: confs[idx]))

    container_kept = [masks[i] for i in keep_indices if tags[i] in SPECIFIC_TAGS]
    final_indices  = []
    for i in keep_indices:
        if tags[i] in FOOD_ONLY_TAGS:
            if any(_mask_containment(masks[i], c) >= containment_threshold
                   for c in container_kept):
                continue
        final_indices.append(i)

    if not final_indices:
        return _empty_dets(), []

    return Detections(
        xyxy       = np.array([xyxys[i] for i in final_indices]),
        confidence = np.array([confs[i]  for i in final_indices]),
        mask       = np.array([masks[i]  for i in final_indices]),
    ), [tag_name.get(tags[i], f"prompt_{tags[i]}") for i in final_indices]  # [FIX 10]


# ════════════════════════════════════════════════════════════════════════════
# PCA geometry  (pure maths, no I/O)
# ════════════════════════════════════════════════════════════════════════════

def pca_geometry(mask: np.ndarray):
    ys, xs   = np.where(mask)
    coords   = np.stack([xs, ys], axis=1).astype(np.float32)
    center   = coords.mean(axis=0)
    pca      = skPCA(n_components=2).fit(coords)
    stds     = np.sqrt(pca.explained_variance_)
    width_px  = 4.0 * stds[0]
    height_px = 4.0 * stds[1]
    pc1       = pca.components_[0]
    angle_deg = np.degrees(np.arctan2(pc1[1], pc1[0]))
    return center, (width_px, height_px), angle_deg, pca.components_


# ════════════════════════════════════════════════════════════════════════════
# Coin scale extraction
# ════════════════════════════════════════════════════════════════════════════

def extract_coin_scale(coin_dets: Detections, img_np: np.ndarray,
                       save_dir: str) -> float:
    if coin_dets is None or len(coin_dets) == 0:
        raise CoinNotFoundError(
            "No coin detected in the image.\n\n"
            "Please include a ₹10 RBI coin (flat, unobstructed) in the photo "
            "and try again. The coin is used as a size reference to estimate "
            "the physical dimensions of each food item."
        )

    best_idx  = int(np.argmax(coin_dets.confidence))
    coin_mask = coin_dets.mask[best_idx]
    coin_xyxy = coin_dets.xyxy[best_idx]

    if coin_mask.sum() < 50:
        raise CoinNotFoundError(
            "Coin mask is too small — the coin may be partially out of frame "
            "or occluded. Please ensure the ₹10 coin is fully visible and "
            "lying flat, then try again."
        )

    _, (w_px, h_px), _, _ = pca_geometry(coin_mask)
    major_px  = max(w_px, h_px)   # always the larger axis = true diameter
    minor_px  = min(w_px, h_px)
    roundness = minor_px / major_px if major_px > 0 else 0

    if roundness < 0.6:
        print(f"  WARNING: coin may be tilted (roundness={roundness:.2f}).")

    px_per_cm = major_px / COIN_DIAMETER_CM
    print(f"  Coin  major={major_px:.1f}px  minor={minor_px:.1f}px  "
          f"roundness={roundness:.2f}  =>  {px_per_cm:.3f} px/cm")

    x1, y1, x2, y2 = map(int, coin_xyxy)
    c_img  = img_np[y1:y2, x1:x2]
    c_mask = coin_mask[y1:y2, x1:x2]
    c_ctr, (cm_w, cm_h), c_ang, _ = pca_geometry(c_mask)

    fig = Figure(figsize=(4, 4))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    ax.imshow(c_img)
    ov = np.zeros((*c_mask.shape, 4), dtype=np.float32)
    ov[c_mask] = [1.0, 0.85, 0.0, 0.4]
    ax.imshow(ov)
    ax.add_patch(Ellipse(
        xy=c_ctr, width=cm_w, height=cm_h, angle=c_ang,
        edgecolor="#ffcc00", facecolor="none", linewidth=2.5
    ))
    ax.plot(*c_ctr, "o", color="white", markersize=7,
            markeredgecolor="#333", markeredgewidth=1.5)
    ax.set_title(f"Coin: {major_px:.0f}px = {COIN_DIAMETER_CM}cm  "
                 f"=> {px_per_cm:.2f} px/cm", fontsize=9)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(save_dir, "coin_debug.png"), dpi=120, bbox_inches="tight")

    return px_per_cm


# ════════════════════════════════════════════════════════════════════════════
# ConvNeXtV2 classification
# ════════════════════════════════════════════════════════════════════════════

def classify_crop(crop_rgb: np.ndarray,
                  conf_thresh: float = CONVNEXT_CONF_THRESH):
    """Classify an RGB numpy crop. Returns (class_name, confidence)."""
    cls_model, idx_to_class, inference_tf = get_classifier()
    device = get_device()
    tensor = inference_tf(image=crop_rgb)["image"].unsqueeze(0)
    tensor = tensor.to(device, memory_format=torch.channels_last)
    autocast_device = "cuda" if device == "cuda" else "cpu"
    with torch.no_grad(), torch.amp.autocast(autocast_device):
        probs = torch.softmax(cls_model(tensor), dim=1)[0]
    top_prob, top_idx = probs.max(0)
    conf = top_prob.item()
    if conf < conf_thresh:
        return None, conf
    return idx_to_class[top_idx.item()], conf


# ════════════════════════════════════════════════════════════════════════════
# PCA image  (internal — sent to LLM, never shown to user)
# ════════════════════════════════════════════════════════════════════════════

def _save_pca_image_for_llm(item: dict, pixels_per_cm: float,
                             seg_idx: int, save_dir: str) -> dict | None:
    crop_mask = item["crop_mask"]
    crop_img  = item["crop_img"]

    if crop_mask.sum() < 50:
        print(f"  SKIP {item['food_class']} — too few mask pixels")
        return None

    center, (width_px, height_px), angle_deg, comps = pca_geometry(crop_mask)

    # [FIX 7] Keep as float — meaningful decimal precision for the LLM prompt
    # Sort: major_cm is always the larger dimension, minor_cm always the smaller
    major_cm = float(f"{float(max(width_px, height_px)) / pixels_per_cm:.1f}")
    minor_cm = float(f"{float(min(width_px, height_px)) / pixels_per_cm:.1f}")

    print(f"  {item['food_class']:<24}  major={major_cm} cm  minor={minor_cm} cm")

    fig = Figure(figsize=(6, 6))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    ax.imshow(crop_img)

    ov = np.zeros((*crop_mask.shape, 4), dtype=np.float32)
    ov[crop_mask] = [0.2, 0.6, 1.0, 0.35]
    ax.imshow(ov)

    cx, cy = center
    ax.add_patch(Ellipse(
        xy=(cx, cy), width=width_px, height=height_px, angle=angle_deg,
        edgecolor="#00d4ff", facecolor="none", linewidth=2, linestyle="--"
    ))

    pc1 = comps[0]; hw = width_px / 2
    ax.annotate("",
        xy=(cx + pc1[0]*hw, cy + pc1[1]*hw),
        xytext=(cx - pc1[0]*hw, cy - pc1[1]*hw),
        arrowprops=dict(arrowstyle="<->", color="#ff4444", lw=2))
    ax.text(cx + pc1[0]*hw + 4, cy + pc1[1]*hw - 8, f"W={major_cm} cm",
            color="#cc0000", fontsize=9, fontweight="bold",
            bbox=dict(facecolor="white", alpha=0.75, pad=2, edgecolor="none"))

    pc2 = comps[1]; hh = height_px / 2
    ax.annotate("",
        xy=(cx + pc2[0]*hh, cy + pc2[1]*hh),
        xytext=(cx - pc2[0]*hh, cy - pc2[1]*hh),
        arrowprops=dict(arrowstyle="<->", color="#44ff88", lw=2))
    ax.text(cx + pc2[0]*hh + 4, cy + pc2[1]*hh + 4, f"H={minor_cm} cm",
            color="#007733", fontsize=9, fontweight="bold",
            bbox=dict(facecolor="white", alpha=0.75, pad=2, edgecolor="none"))

    ax.plot(cx, cy, "o", color="white", markersize=6,
            markeredgecolor="#333", markeredgewidth=1.5)
    ax.set_title(
    f"{item['food_class']}  conf={item['cls_conf']:.2f}   "
    f"major={major_cm} cm  |  minor={minor_cm} cm", fontsize=10)
    ax.axis("off")
    fig.tight_layout()

    safe_class = re.sub(r'[^A-Za-z0-9_]', '_', item['food_class'])
    pca_path = os.path.join(save_dir, f"pca_{seg_idx:02d}_{safe_class}.png")
    fig.savefig(pca_path, dpi=130, bbox_inches="tight")

    return {
        "seg_idx":      seg_idx,
        "food_class":   item["food_class"],
        "cls_conf":     item["cls_conf"],
        "major_cm":     major_cm,
        "minor_cm":     minor_cm,         # float now [FIX 7]
        "pca_img_path": pca_path,
        "crop_img":     crop_img,
        "crop_mask":    crop_mask,
    }


# ════════════════════════════════════════════════════════════════════════════
# Segmented crop image
# ════════════════════════════════════════════════════════════════════════════

_PALETTE = [
    (0.20, 0.78, 0.35), (0.26, 0.63, 0.93), (0.98, 0.55, 0.18),
    (0.86, 0.20, 0.27), (0.61, 0.35, 0.71), (0.98, 0.84, 0.10),
    (0.12, 0.73, 0.73), (0.95, 0.37, 0.62),
]

def _item_color(idx: int):
    return _PALETTE[idx % len(_PALETTE)]


def save_segmented_crop(item: dict, seg_idx: int, save_dir: str,
                        weight_g: float | None = None) -> str:
    crop_img  = item["crop_img"]
    crop_mask = item["crop_mask"]
    color     = _item_color(seg_idx)

    fig = Figure(figsize=(4, 4))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)

    dimmed = crop_img.copy().astype(np.float32)
    dimmed[~crop_mask] *= 0.25
    ax.imshow(dimmed.astype(np.uint8))

    ov = np.zeros((*crop_mask.shape, 4), dtype=np.float32)
    ov[crop_mask] = [*color, 0.30]
    ax.imshow(ov)

    title = item["food_class"]
    if weight_g is not None:
        title += f"  ·  {weight_g:.0f} g"
    ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
    ax.axis("off")
    fig.tight_layout()

    safe_class = re.sub(r'[^A-Za-z0-9_]', '_', item['food_class'])
    path = os.path.join(save_dir, f"seg_{seg_idx:02d}_{safe_class}.png")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    return path


def save_combined_annotated_image(image_pil: Image.Image,
                                  final_results: list,
                                  full_masks: list,
                                  save_dir: str) -> str:
    img_np = np.array(image_pil.convert("RGB"))
    H, W   = img_np.shape[:2]

    fig = Figure(figsize=(max(8, min(W / 100, 14)),
                          max(6, min(H / 100, 10))), dpi=120)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    ax.imshow(img_np)

    for idx, (res, mask) in enumerate(zip(final_results, full_masks)):
        color = _item_color(idx)
        ov = np.zeros((H, W, 4), dtype=np.float32)
        ov[mask] = [*color, 0.38]
        ax.imshow(ov)

        ys, xs = np.where(mask)
        if len(xs) == 0:
            continue
        cx, cy = float(xs.mean()), float(ys.mean())
        ax.text(cx, cy,
                f"{res['food_class']}\n{res['weight_g']:.0f} g",
                ha="center", va="center",
                fontsize=max(7, min(11, W // 80)),
                fontweight="bold", color="white",
                bbox=dict(boxstyle="round,pad=0.35",
                          facecolor=color, alpha=0.82,
                          edgecolor="white", linewidth=0.8))

    ax.axis("off")
    fig.tight_layout(pad=0)
    path = os.path.join(save_dir, "annotated_result.png")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    return path


# ════════════════════════════════════════════════════════════════════════════
# LLM weight estimation
# ════════════════════════════════════════════════════════════════════════════

class WeightEstimate(BaseModel):
    weight_g: float = Field(
        description="Single best-estimate weight of the food portion in grams.")
    geometry: str = Field(
        description="Geometric shape assumed (e.g. 'hemisphere', 'cylinder', 'flat disc').")
    density_g_per_cm3: float = Field(
        description="The density value provided in Step 3 — copy it verbatim, do NOT change it.")
    reasoning: str = Field(
        description="One sentence showing which shape was chosen and the volume formula used.")
    # [FIX 2] Declared as a proper Pydantic Field — not a dynamic attribute assignment
    density_source: str = Field(
        default="",
        description="Internal field — populated by pipeline code, not by the LLM.")


_parser = PydanticOutputParser(pydantic_object=WeightEstimate)

_llm = ChatOllama(
    base_url=OLLAMA_BASE_URL,
    model=OLLAMA_MODEL,
    temperature=0,
    seed=42,
    reasoning=True,
)


def _img_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def estimate_weight(item: dict) -> WeightEstimate:
    density_val, density_src = _get_density(item["food_class"])  # ← unpack tuple
    b64 = _img_b64(item["pca_img_path"])

    prompt = (
        f"You are a food portion weight estimation expert.\n\n"
        f"Food item: {item['food_class']}\n\n"
        f"Step 1 — Measured dimensions (from PCA + calibrated coin scale):\n"
        f"  • Major axis (longer dimension): {item['major_cm']} cm\n"
        f"  • Minor axis (shorter dimension): {item['minor_cm']} cm\n\n"
        f"Step 2 — Visual reference:\n"
        f"The attached image shows the segmented food item with its PCA ellipse overlay. "
        f"The red arrow is the major axis and the green arrow is the minor axis. "
        f"Use the numeric dimensions above as the authoritative measurements.\n\n"
        f"Step 3 — Density (authoritative, from food science database — do NOT change this):\n"
        f"  • food_class        = {item['food_class']}\n"
        f"  • density_g_per_cm3 = {density_val:.4f}  ← copy this verbatim into your output\n\n"
        f"Step 4 — Estimate the weight of this food portion.\n"
        f"Decide yourself which axis represents length, width, or height based on "
        f"the food's shape and the visual reference image.\n"
        f"Choose a realistic geometric model (hemisphere, cylinder, sphere, flat disc, etc.), "
        f"compute volume from the given dimensions, "
        f"then multiply by the density value from Step 3 above.\n"
        f"weight_g = volume_cm3 × {density_val:.4f}\n\n"
        f"{_parser.get_format_instructions()}"
    )

    msg = HumanMessage(content=[
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        {"type": "text", "text": prompt},
    ])

    try:
        raw_response = _llm.invoke(
            [msg],
        )
        result = _parser.invoke(raw_response)
    except TypeError:
        raw_response = _llm.invoke([msg])
        result = _parser.invoke(raw_response)
    except (OutputParserException, Exception) as exc:
        print(f"  [estimate_weight] parse failed for '{item['food_class']}': {exc}")
        result = WeightEstimate(
            weight_g=100.0,
            geometry="unknown (parse error)",
            density_g_per_cm3=density_val,
            reasoning=f"Defaulted to 100 g — LLM parse error: {str(exc)[:120]}",
            density_source=density_src,   # ← now always defined
        )
        return result

    result.density_g_per_cm3 = density_val   # hard-enforce
    result.density_source = density_src       # ← now always defined
    return result

# ════════════════════════════════════════════════════════════════════════════
# Nutrition scaling
# ════════════════════════════════════════════════════════════════════════════


def scale_nutrition(food_class: str, weight_g: float) -> dict | None:
    key = food_class.strip().lower()
    entry = NUTRITION_DB.get(key)
    if entry is None:
        raise KeyError(
            f"[nutrition] '{key}' not found in food_nutrition.json. "
            f"Add it before running inference."
        )
    factor = weight_g / 100.0
    scaled = {"food_class": food_class, "weight_g": round(weight_g, 1)}
    for col in NUTRIENT_COLS:
        raw_val = entry.get(col)
        scaled[col] = round(raw_val * factor, 2) if raw_val is not None else None
    return scaled

# ════════════════════════════════════════════════════════════════════════════
# Shared classification + geometry helper
# ════════════════════════════════════════════════════════════════════════════

def _classify_and_crop(img_np, food_dets, food_labels):
    """Run ConvNeXtV2 on every food detection. Returns list of result dicts."""
    results = []
    for i, (mask, xyxy, label) in enumerate(
            zip(food_dets.mask, food_dets.xyxy, food_labels)):
        H_img, W_img = img_np.shape[:2]
        x1 = max(0, int(xyxy[0]))
        y1 = max(0, int(xyxy[1]))
        x2 = min(W_img, int(xyxy[2]))
        y2 = min(H_img, int(xyxy[3]))
        crop_mask     = mask[y1:y2, x1:x2]
        original_crop = img_np[y1:y2, x1:x2].copy()
        masked_crop   = original_crop.copy()
        masked_crop[~crop_mask] = 128   # neutral grey hides adjacent food
        food_class, conf = classify_crop(masked_crop)
        if food_class:
            results.append({
                "seg_idx":    i,
                "sam_label":  label,
                "food_class": food_class,
                "cls_conf":   conf,
                "mask":       mask,          # full-image mask
                "xyxy":       xyxy,
                "crop_img":   original_crop,
                "crop_mask":  crop_mask,     # bbox-cropped mask
            })
    return results


def _llm_and_nutrition(pca_data, convnext_results, save_dir):
    """
    Run LLM weight estimation + nutrition lookup for every pca_data item.
    Returns (final_results, full_masks).
    """
    final_results = []

    # [FIX 11] Index full-image masks by seg_idx — never silently lose the
    #          annotated image because of a seg_idx mismatch.
    mask_by_seg = {r["seg_idx"]: r["mask"] for r in convnext_results}

    for item in pca_data:
        print(f"\n[{item['seg_idx']}] {item['food_class']} ...")
        est       = estimate_weight(item)
        nutrition = scale_nutrition(item["food_class"], est.weight_g)
        seg_path  = save_segmented_crop(item, item["seg_idx"], save_dir,
                                        weight_g=est.weight_g)

        final_results.append({
            "seg_idx":        item["seg_idx"],
            "food_class":     item["food_class"],
            "cls_conf":       item["cls_conf"],
            "major_cm":       item["major_cm"],
            "minor_cm":       item["minor_cm"],
            "weight_g":       est.weight_g,
            "geometry":       est.geometry,
            "density":        est.density_g_per_cm3,
            "density_source": est.density_source,   # [FIX 5] now in the dict
            "reasoning":      est.reasoning,
            "nutrition":      nutrition,
            "seg_img_path":   seg_path,
        })

    # Build aligned lists — skip items whose mask was not found [FIX 11]
    paired = [(r, mask_by_seg[r["seg_idx"]])
              for r in final_results
              if r["seg_idx"] in mask_by_seg]

    if not paired:
        return final_results, []

    aligned_results, full_masks = zip(*paired)
    return list(aligned_results), list(full_masks)


# ════════════════════════════════════════════════════════════════════════════
# Streaming entry point  (used by Gradio for live step progress)
# ════════════════════════════════════════════════════════════════════════════

_STEP_LABELS = [
    "SAM3 Segmentation",        # 1
    "Coin Scale Detection",     # 2
    "Food Classification",      # 3
    "PCA Geometry",             # 4
    "Weight & Nutrition",       # 5
]
N_STEPS = len(_STEP_LABELS)


def run_pipeline_steps(image_pil: Image.Image, save_dir: str):
    """
    Generator — yields (step_index, step_label, partial) after each stage.
    partial is None for mid-pipeline yields;
    (final_results, annotated_path, error_msg) on the last yield.
    """
    


    # ── 1. SAM3 ───────────────────────────────────────────────────────────
    yield (1, _STEP_LABELS[0], None)

    # Resize large uploads to SAM3's native resolution before any GPU work.
    # Phone photos (3000–4000px+) OOM on 4× sequential SAM passes; test images
    # are already small. This is the primary cause of CUDA OOM for uploads.
    sam_image = _resize_for_sam(image_pil)
    img_np = np.array(sam_image.convert("RGB"))

    det1 = get_dets(sam_image, PROMPT_1)
    if torch.cuda.is_available(): torch.cuda.empty_cache()

    det2 = get_dets(sam_image, PROMPT_2)
    if torch.cuda.is_available(): torch.cuda.empty_cache()

    det3 = get_dets(sam_image, PROMPT_3)
    if torch.cuda.is_available(): torch.cuda.empty_cache()

    coin_dets = get_dets(sam_image, PROMPT_COIN, conf_thresh=COIN_CONF_THRESH)
    if torch.cuda.is_available(): torch.cuda.empty_cache()










    print(f"Food raw → P1:{len(det1)}  P2:{len(det2)}  P3:{len(det3)}")
    print(f"Coin     → {len(coin_dets)}")

    food_dets, food_labels = merge_detections(
        det1, det2, det3,
        prompt_labels=[PROMPT_1, PROMPT_2, PROMPT_3],
        iou_threshold=IOU_THRESH,
        containment_threshold=CONT_THRESH,
    )
    print(f"Food after merge → {len(food_dets)} segments")

    # ── 2. Coin scale ──────────────────────────────────────────────────────
    yield (2, _STEP_LABELS[1], None)
    try:
        pixels_per_cm = extract_coin_scale(coin_dets, img_np, save_dir)
    except CoinNotFoundError as e:
        yield (N_STEPS, _STEP_LABELS[-1], ([], None, str(e)))
        return

    # ── 3. Classification ──────────────────────────────────────────────────
    yield (3, _STEP_LABELS[2], None)
    convnext_results = _classify_and_crop(img_np, food_dets, food_labels)
    print(f"Kept {len(convnext_results)} / {len(food_dets)} after ConvNeXtV2")

    if not convnext_results:
        yield (N_STEPS, _STEP_LABELS[-1], ([], None,
               "No food items were recognised with sufficient confidence."))
        return

    # ── 4. PCA geometry ────────────────────────────────────────────────────
    yield (4, _STEP_LABELS[3], None)
    pca_data = []
    for item in convnext_results:
        result = _save_pca_image_for_llm(item, pixels_per_cm,
                                         item["seg_idx"], save_dir)
        if result:
            pca_data.append(result)

    if not pca_data:
        yield (N_STEPS, _STEP_LABELS[-1], ([], None,
               "PCA geometry failed for all detected items."))
        return



    # ── 5. LLM weight + nutrition ──────────────────────────────────────────
    yield (5, _STEP_LABELS[4], None)
    final_results, full_masks = _llm_and_nutrition(
        pca_data, convnext_results, save_dir)

    annotated_path = None
    if final_results and full_masks:
        annotated_path = save_combined_annotated_image(
            sam_image,          # ← was image_pil; must match mask dimensions
            final_results, full_masks, save_dir)

    yield (N_STEPS, _STEP_LABELS[-1], (final_results, annotated_path, None))


# ════════════════════════════════════════════════════════════════════════════
# Non-streaming entry point  (kept for scripts / tests)
# ════════════════════════════════════════════════════════════════════════════

def run_pipeline(image_pil: Image.Image, save_dir: str):
    """Blocking wrapper around run_pipeline_steps."""
    result = ([], None, None)
    for _, _, partial in run_pipeline_steps(image_pil, save_dir):
        if partial is not None:
            result = partial
    return result
