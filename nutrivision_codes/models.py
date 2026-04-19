"""
models.py  —  Lazy loading of SAM3 and ConvNeXtV2.

Both models are loaded once on the first call and cached globally.

"""

import albumentations as A
import timm
import torch
from albumentations.pytorch import ToTensorV2
from config import CKPT_PATH
from transformers import Sam3Model, Sam3Processor

# ── Globals (populated on first use) ──────────────────────────────────────
_device = None
_sam_model = None
_sam_processor = None
_cls_model = None
_idx_to_class = None
_inference_tf = None


def get_device() -> str:
    global _device
    if _device is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
    return _device


def get_sam():
    """Return (sam_model, sam_processor), loading on first call."""
    global _sam_model, _sam_processor
    if _sam_model is None:
        device = get_device()
        print(f"[models] Loading SAM3 on {device} ...")
        _sam_model = Sam3Model.from_pretrained("facebook/sam3").to(device)
        _sam_processor = Sam3Processor.from_pretrained("facebook/sam3")
        print("[models] SAM3 ready.")
    return _sam_model, _sam_processor


def get_classifier():
    """Return (cls_model, idx_to_class, inference_transform), loading on first call."""
    global _cls_model, _idx_to_class, _inference_tf
    if _cls_model is None:
        device = get_device()
        print(f"[models] Loading ConvNeXtV2 from '{CKPT_PATH}' ...")
        ckpt = torch.load(CKPT_PATH, map_location=device, weights_only=False)

        class_to_idx = ckpt["class_to_idx"]
        _idx_to_class = {v: k for k, v in class_to_idx.items()}
        num_classes = ckpt["cfg"]["num_classes"]
        img_size = ckpt["cfg"]["img_size"]
        model_name = ckpt["cfg"]["model_name"]

        _cls_model = timm.create_model(
            model_name, pretrained=False, num_classes=num_classes, drop_rate=0.0
        )
        _cls_model.load_state_dict(ckpt["model_state"])
        _cls_model = _cls_model.to(device, memory_format=torch.channels_last)
        _cls_model.eval()

        MEAN = [0.485, 0.456, 0.406]
        STD = [0.229, 0.224, 0.225]
        _inference_tf = A.Compose(
            [
                A.Resize(height=int(img_size * 1.14), width=int(img_size * 1.14)),
                A.CenterCrop(height=img_size, width=img_size),
                A.Normalize(mean=MEAN, std=STD),
                ToTensorV2(),
            ]
        )

        print(
            f"[models] ConvNeXtV2 ready — {num_classes} classes: "
            f"{list(class_to_idx.keys())}"
        )

    return _cls_model, _idx_to_class, _inference_tf
