"""
app.py  —  Gradio frontend for the Food Nutrition Estimator.

"""

import os
import shutil
import tempfile
import threading
import time

import gradio as gr
import pandas as pd
from config import NUTRIENT_COLS, NUTRIENT_LABELS
from PIL import Image
from pipeline import N_STEPS, run_pipeline_steps

# ── Example images ─────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMPLE_DIR = os.path.join(BASE_DIR, "test_images")

os.makedirs(EXAMPLE_DIR, exist_ok=True)
_example_files = [
    os.path.join(EXAMPLE_DIR, f)
    for f in sorted(os.listdir(EXAMPLE_DIR))
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
]
EXAMPLES = [[p] for p in _example_files]

# ── Supported food classes ──────────────────────────────────────────────────
SUPPORTED_FOODS = [
    "aloo gobi",
    "aloo methi",
    "aloo mutter",
    "aloo paratha",
    "amritsari kulcha",
    "anda curry",
    "balushahi",
    "banana chips",
    "besan laddu",
    "bhindi masala",
    "biryani",
    "boondi laddu",
    "chaas",
    "chana masala",
    "chapati",
    "chicken pizza",
    "chicken wings",
    "chikki",
    "chivda",
    "chole bhature",
    "dabeli",
    "dal khichdi",
    "dhokla",
    "falooda",
    "fish curry",
    "gajar ka halwa",
    "garlic bread",
    "garlic naan",
    "ghevar",
    "grilled sandwich",
    "gujhia",
    "gulab jamun",
    "hara bhara kabab",
    "idiyappam",
    "idli",
    "jalebi",
    "kaju katli",
    "khakhra",
    "kheer",
    "kulfi",
    "margherita pizza",
    "masala dosa",
    "masala papad",
    "medu vada",
    "misal pav",
    "modak",
    "moong dal halwa",
    "murukku",
    "mysore pak",
    "navratan korma",
    "neer dosa",
    "onion pakoda",
    "palak paneer",
    "paneer masala",
    "paneer pizza",
    "pani puri",
    "paniyaram",
    "papdi chaat",
    "patrode",
    "pav bhaji",
    "pepperoni pizza",
    "phirni",
    "poha",
    "pongal",
    "puri bhaji",
    "rajma chawal",
    "rasgulla",
    "rava dosa",
    "sabudana khichdi",
    "sabudana vada",
    "samosa",
    "seekh kebab",
    "set dosa",
    "sev puri",
    "solkadhi",
    "steamed momo",
    "thukpa",
    "uttapam",
    "vada pav",
]

_CATEGORY_MAP = {
    "Breads & Rice": [
        "aloo paratha",
        "amritsari kulcha",
        "chapati",
        "garlic bread",
        "garlic naan",
        "idiyappam",
        "neer dosa",
        "biryani",
        "dal khichdi",
        "rajma chawal",
        "set dosa",
        "rava dosa",
        "masala dosa",
        "uttapam",
        "poha",
        "pongal",
        "sabudana khichdi",
    ],
    "Snacks & Chaat": [
        "banana chips",
        "chivda",
        "chikki",
        "dabeli",
        "dhokla",
        "hara bhara kabab",
        "khakhra",
        "masala papad",
        "misal pav",
        "murukku",
        "onion pakoda",
        "pani puri",
        "papdi chaat",
        "pav bhaji",
        "samosa",
        "sabudana vada",
        "sev puri",
        "vada pav",
        "grilled sandwich",
        "chicken wings",
        "steamed momo",
        "seekh kebab",
        "idli",
        "medu vada",
        "paniyaram",
        "patrode",
    ],
    "Curries & Mains": [
        "aloo gobi",
        "aloo methi",
        "aloo mutter",
        "anda curry",
        "bhindi masala",
        "chana masala",
        "chole bhature",
        "fish curry",
        "navratan korma",
        "palak paneer",
        "paneer masala",
        "puri bhaji",
        "thukpa",
    ],
    "Sweets & Desserts": [
        "balushahi",
        "besan laddu",
        "boondi laddu",
        "falooda",
        "gajar ka halwa",
        "ghevar",
        "gujhia",
        "gulab jamun",
        "jalebi",
        "kaju katli",
        "kheer",
        "kulfi",
        "modak",
        "moong dal halwa",
        "mysore pak",
        "phirni",
        "rasgulla",
    ],
    "Pizza": ["chicken pizza", "margherita pizza", "paneer pizza", "pepperoni pizza"],
    "Drinks": ["chaas", "solkadhi"],
}


def _build_foods_html() -> str:
    cat_html_parts = []
    for cat, dishes in _CATEGORY_MAP.items():
        emoji_map = {
            "Breads & Rice": "🍚",
            "Snacks & Chaat": "🥙",
            "Curries & Mains": "🍛",
            "Sweets & Desserts": "🍮",
            "Pizza": "🍕",
            "Drinks": "🥤",
        }
        emoji = emoji_map.get(cat, "🍽️")
        pills = "".join(
            f'<span style="display:inline-block;margin:3px 4px;padding:5px 12px;'
            f"border-radius:20px;font-size:0.82rem;font-weight:500;"
            f"background:var(--pill-bg,#f0faf4);color:var(--pill-fg,#1a6640);"
            f'border:1px solid var(--pill-border,#b7e4ca);white-space:nowrap;">'
            f"{d.title()}</span>"
            for d in sorted(dishes)
        )
        cat_html_parts.append(
            f'<div style="margin-bottom:18px;">'
            f'<div style="font-size:0.78rem;font-weight:700;letter-spacing:0.08em;'
            f'text-transform:uppercase;color:#555;margin-bottom:6px;">'
            f"{emoji} {cat}</div>"
            f'<div style="display:flex;flex-wrap:wrap;gap:0;">{pills}</div>'
            f"</div>"
        )
    return f"""
<div style="font-family:'Segoe UI',system-ui,sans-serif;max-width:900px;margin:0 auto;padding:8px 0;">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;
              padding:16px 20px;border-radius:12px;
              background:linear-gradient(135deg,#e8f8ee 0%,#f3fdf6 100%);
              border:1px solid #c3ebd4;">
    <span style="font-size:2.2rem;">🍽️</span>
    <div>
      <div style="font-size:1.15rem;font-weight:700;color:#1a4d2e;">
        {len(SUPPORTED_FOODS)} Recognised Dishes
      </div>
      <div style="font-size:0.82rem;color:#4a7c5a;margin-top:2px;">
        The model can identify and estimate nutrition for any of the dishes below.
        Place a <strong>₹10 coin</strong> flat in frame for accurate weight estimation.
      </div>
    </div>
  </div>
  {"".join(cat_html_parts)}
  <div style="margin-top:16px;padding:10px 14px;border-radius:8px;
              background:#fffbec;border:1px solid #ffe082;
              font-size:0.78rem;color:#7a5c00;">
    ⚠️ Items not in this list will be skipped during classification.
    Confidence threshold: 50% (ConvNeXtV2).
  </div>
</div>
"""


# ════════════════════════════════════════════════════════════════════════════
# Session helpers
# ════════════════════════════════════════════════════════════════════════════


def _new_session_dir() -> str:
    return tempfile.mkdtemp(prefix="food_nutr_")


def _cleanup_session(session_dir: str | None) -> None:
    if session_dir and os.path.isdir(session_dir):
        shutil.rmtree(session_dir, ignore_errors=True)


def _prune_old_temp_dirs() -> None:
    temp_base = tempfile.gettempdir()
    while True:
        now = time.time()
        try:
            for name in os.listdir(temp_base):
                if not name.startswith("food_nutr_"):
                    continue
                path = os.path.join(temp_base, name)
                if os.path.isdir(path) and (now - os.path.getmtime(path)) > 3600:
                    shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass
        time.sleep(3600)


threading.Thread(target=_prune_old_temp_dirs, daemon=True).start()


# ════════════════════════════════════════════════════════════════════════════
# Progress text builder
# ════════════════════════════════════════════════════════════════════════════

_STEP_LABELS = [
    "SAM3 Segmentation",
    "Coin Scale Detection",
    "Food Classification",
    "PCA Geometry",
    "Weight & Nutrition Estimation",
]


def _progress_md(current_step: int, done: bool = False, error: bool = False) -> str:
    lines = []
    for i, label in enumerate(_STEP_LABELS, start=1):
        if done or i < current_step:
            lines.append(f"✅  ~~{label}~~")
        elif i == current_step:
            lines.append(f"❌  **{label}**" if error else f"⏳  **{label}** …")
        else:
            lines.append(f"⬜  {label}")
    return "\n\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# Nutrition table builder
# ════════════════════════════════════════════════════════════════════════════


def _build_table(results: list) -> pd.DataFrame:
    rows = []
    for r in results:
        nut = r.get("nutrition") or {}
        row = {
            "Food": r["food_class"],
            "Weight (g)": f"{r['weight_g']:.0f}",
        }
        for col, label in zip(NUTRIENT_COLS, NUTRIENT_LABELS):
            val = nut.get(col)
            row[label] = f"{val:.1f}" if val is not None else "—"
        rows.append(row)
    return pd.DataFrame(rows)


# ════════════════════════════════════════════════════════════════════════════
# Core callback  (generator — streams progress then final result)
# ════════════════════════════════════════════════════════════════════════════


def process_image(image, session_dir: str | None):
    _cleanup_session(session_dir)
    new_dir = _new_session_dir()

    if image is None:
        yield (
            "⚠️ **No image provided.** Upload a photo or use the camera.",
            None,
            pd.DataFrame(),
            "",
            new_dir,
        )
        return

    pil_img = Image.fromarray(image)

    try:
        for step_idx, _step_label, partial in run_pipeline_steps(pil_img, new_dir):

            if partial is None:
                yield (_progress_md(step_idx), None, pd.DataFrame(), "", new_dir)

            else:
                final_results, annotated_path, error = partial

                if error:
                    yield (
                        _progress_md(step_idx, error=True) + f"\n\n⚠️ **{error}**",
                        None,
                        pd.DataFrame(),
                        "",
                        new_dir,
                    )
                    return

                if not final_results:
                    yield (
                        _progress_md(N_STEPS, done=True)
                        + "\n\n⚠️ **No food items detected with sufficient confidence.**",
                        None,
                        pd.DataFrame(),
                        "",
                        new_dir,
                    )
                    return

                n = len(final_results)
                # [FIX 4] Correct field name: calories_kcal (was energy_kcal — always 0)
                total_kcal = sum(
                    (r.get("nutrition") or {}).get("calories_kcal", 0) or 0
                    for r in final_results
                )
                kcal_str = f" · **{total_kcal:.0f} kcal** total" if total_kcal else ""
                summary = (
                    f"\n\n**{n} food item{'s' if n > 1 else ''} detected**{kcal_str}"
                )

                annotated_img = (
                    annotated_path
                    if annotated_path and os.path.exists(annotated_path)
                    else None
                )

                table_df = _build_table(final_results)

                reasoning_parts = []
                for r in final_results:
                    # [FIX 5] density_source now correctly populated from result dict
                    density_src = r.get("density_source", "—")
                    # 📋 = looked up from JSON,  🧠 = default fallback
                    density_icon = "📋" if "food_density" in density_src else "🧠"
                    reasoning_parts.append(
                        f"### {r['food_class']}  _(conf {r['cls_conf']:.0%})_\n"
                        f"- **Weight:** {r['weight_g']:.0f} g\n"
                        f"- **Dimensions:** major={r.get('major_cm', '?')} cm  ·  minor={r.get('minor_cm', '?')} cm\n"
                        f"- **Geometry:** {r['geometry']}\n"
                        f"- **Density:** {r['density']:.3f} g/cm³  "
                        f"{density_icon} _{density_src}_\n"
                        f"- **Reasoning:** {r['reasoning']}\n"
                    )
                reasoning_md = "\n---\n".join(reasoning_parts)

                yield (
                    _progress_md(N_STEPS, done=True) + summary,
                    annotated_img,
                    table_df,
                    reasoning_md,
                    new_dir,
                )

    except Exception as exc:
        yield (f"❌ **Pipeline error:** {exc}", None, pd.DataFrame(), "", new_dir)


# ════════════════════════════════════════════════════════════════════════════
# Gradio UI
# ════════════════════════════════════════════════════════════════════════════

DESCRIPTION = """
## 🍽️ Food Nutrition Estimator

Upload a plate photo **with a ₹10 coin** as a size reference, or use your camera.

Best result with 2 major axis clearly visible 

**Pipeline:** SAM3 segmentation → ConvNeXtV2 classification → PCA geometry → LLM weight estimation → Nutrition lookup

> The ₹10 coin must be clearly visible and lying flat for accurate size calibration.
See the Pipeline Progress Below after Analyze button pressed
"""

with gr.Blocks(title="Food Nutrition Estimator", theme=gr.themes.Soft()) as demo:

    session_dir_state = gr.State(value=None)

    gr.Markdown(DESCRIPTION)

    with gr.Tabs():

        with gr.Tab("🔍 Analyse"):
            with gr.Row(equal_height=True):
                with gr.Column(scale=1, min_width=300):
                    image_input = gr.Image(
                        label="📷 Upload photo or use camera",
                        sources=["upload", "webcam"],
                        type="numpy",
                        height=360,
                    )
                    run_btn = gr.Button("🔍 Analyse", variant="primary", size="lg")
                    if EXAMPLES:
                        gr.Examples(
                            examples=EXAMPLES,
                            inputs=image_input,
                            label="📂 Example images",
                        )

                with gr.Column(scale=2, min_width=440):
                    annotated_out = gr.Image(
                        label="🖼️ Detected food items",
                        type="filepath",
                        interactive=False,
                        height=360,
                    )

            progress_out = gr.Markdown(value="*Submit an image to begin.*")

            gr.Markdown("### 📊 Nutrition Summary")
            table_out = gr.Dataframe(
                label=None,
                wrap=True,
                interactive=False,
            )

            with gr.Accordion("📝 LLM Weight Reasoning", open=False):
                reasoning_out = gr.Markdown()

            run_btn.click(
                fn=process_image,
                inputs=[image_input, session_dir_state],
                outputs=[
                    progress_out,
                    annotated_out,
                    table_out,
                    reasoning_out,
                    session_dir_state,
                ],
            )

        with gr.Tab(f"📋 Supported Foods ({len(SUPPORTED_FOODS)})"):
            gr.HTML(_build_foods_html())


if __name__ == "__main__":
    # [FIX 14] queue() must be called before launch() for generator streaming to work.
    # Without it, Gradio buffers all yields and only renders the final state —
    # users see no progress updates, just a long hang then a sudden result.
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7868,
        share=True,
    )
# 7680
