# 🥗 NutriVision — AI-Powered Indian Food Nutrition Estimator

NutriVision is an end-to-end AI system that accepts a photograph of a meal — including complex Indian multi-dish plates — and returns a detailed nutritional breakdown with personalised dietary suggestions. No manual food entry, no fixed 100g assumptions, and full support for Indian cuisine.

---

## 🌐 Live Demo

| Instance | URL |
|---|---|
| **Primary** (more credits) | https://7860-01kp8gvr84ng3myeemyw7vzz46.cloudspaces.litng.ai |
| **Mirror** | https://7860-01knjbx5j5gnvmttvxykcmx4bh.cloudspaces.litng.ai/ |

Both URLs serve the identical Gradio application running on Lightning AI with GPU acceleration.


## Overview

### What It Does

1. Takes a food photograph (with a ₹10 coin in frame for scale calibration)
2. Segments each food item using SAM3
3. Classifies items across 79 Indian food categories (97.92% Top-1 accuracy)
4. Estimates real-world portion weight using PCA geometry + food-specific density
5. Returns a full macro/micronutrient breakdown and personalised dietary suggestions

## Pipeline

```
Input Image
  → SAM3 Segmentation          (pixel masks for food, container, coin)
  → Coin Scale Extraction      (₹10 coin → px/cm calibration factor)
  → ConvNeXtV2 Classification  (79 Indian food classes)
  → PCA Geometry               (rotation-invariant major/minor axes)
  → LLM Weight Estimation      (geometry model × density-enforced lookup)
  → Nutrition Scaling          (per-100g values × estimated weight)
  → Output                     (annotated image + nutrition table + LLM reasoning)
```

The pipeline is a streaming generator — Gradio streams progress after each of 5 stages, so you see live step-by-step feedback rather than waiting for the full result.

---

## Quick Start

### Prerequisites

- Hugging Face account with [SAM3 access](https://huggingface.co/facebook/sam3) approved
- OpenRouter API key (for LLM weight reasoning)

## ⚙️ Running the Project on Lightning AI

Follow these steps to run NutriVision on Lightning AI using Gradio:

---

### 🔑 1. Set Environment Variables

In the Lightning AI platform, go to Environment settings and add:

- `HF_TOKEN` → Your Hugging Face access token  
- `OLLAMA_API_KEY` → Your Ollama / OpenRouter API key  

> These are required for SAM3 model access and LLM-based weight estimation.

---

### 📥 2. Download Model Weights

Before running the app, download the best image classification model:

- The download link is available inside: nutrivision_codes/files_models/model_py.txt

- Place the downloaded `.pt` file in the correct path as defined in `config.py`

---

### ⚡ 3. Enable Gradio (Serverless)

- Use Gradio extension in Lightning AI  
- Enable Serverless mode 
- Set port to: 7860

---

### ▶️ 4. Run the Application

Navigate to the correct directory and run:

'''bash
python nutrivision_codes/app.py

---
### 🌐 5. Access the App

Once running, open: http://localhost:7860
Or use the Lightning AI generated public URL.


### For the deployed Gradio interface:

- Upload a photo of your meal with a ₹10 coin lying flat in frame
- Click Analyse
- Watch the 5-step progress checklist stream live
- View the annotated image, nutrition table, and LLM weight reasoning

## Gradio Interface

![Report](Report/Images/ds1.jpg)

### Gradio Output Interface

![Report](Report/Images/ds4.jpg)

---

## Image Requirements

For best results:

- Place a ₹10 coin flat and clearly visible in frame — the pipeline halts at Step 2 if no coin is detected
- Ensure food items are not heavily occluded
- Use good, even lighting
- Avoid extreme angles (overhead or top-down works best)

> ⚠️ The coin is required for scale calibration. Without it, the pipeline cannot estimate real-world dimensions.

---


## Repository Structure

```
.
├── .gitignore                         # Git ignore rules

├── 📂 Archive/                        # Deprecated / older experiments
│   └── 📂 Deprecated_Experiments/
│       ├── MLP_Training.ipynb
│       ├── YOLO_MLP_Training.ipynb
│       ├── YOLOv12s_Initial_Training.ipynb
│       ├── YOLOv12s_Main_Training.ipynb
│       ├── YOLOv12s_Final_Training.ipynb
│       ├── training_history.csv
│       │
│       ├── 📂 EDA/
│       │   └── Image_Dataset_Eda.ipynb
│       │
│       └── 📂 HyperParameter/
│           └── Convnextv2_Tuning.ipynb

├── 📂 Notebooks/                      # Active notebooks for development
│   ├── 📂 Model Training/
│   │   └── ConvNeXtV2_Training.ipynb
│   │
│   └── 📂 Model evaluation/
│       └── Model_Pipeline_Evaluation.ipynb

├── 📂 Report/                         # Project documentation & reports
│   ├── 📂 Images/                     # Dataset samples & model outputs
│   │   └── (ds images, model outputs, graphs, etc.)
│   │
│   ├── 📄 Milestone Reports
│   │   ├── Milestone_1_Report.md
│   │   ├── Milestone_2_Report.md
│   │   ├── Milestone_4_Report.pdf
│   │   └── Milestone_5_Report.pdf
│   │
│   ├── 📂 Milestone_6/                # Final deliverables
│   │   ├── User Guide.pdf
│   │   ├── Technical Report.pdf
│   │   ├── NutriVision_Non_Technical_Report.md
│   │   └── Developer Guide.md
│   │
│   └── 📂 Contribution/              # Team contributions
│       ├── Milestone1_Contribution.md
│       ├── Milestone2_Contribution.md
│       ├── Milestone3_Contribution.md
│       └── Milestone4_Contribution.md

├── 📂 Presentation/                  # Project presentations
│   ├── Milestone_1.pdf
│   ├── Milestone_2.pptx
│   ├── Milestone_3.pdf
│   ├── Milestone_4.pdf
│   └── Milestone_5.pdf

├── 📂 nutrivision_codes/             # Core application code
│   ├── 📂 files_models/              # Model-related data
│   │   ├── model_py.txt
│   │   ├── food_density.json
│   │   └── food_nutrition.json
│   │
│   ├── 📂 test_images/               # Sample input images
│   │   └── (food image samples)
│   │
│   ├── 🚀 app.py                    # Main application interface
│   ├── 🔄 pipeline.py               # End-to-end pipeline logic
│   ├── 🧠 models.py                 # Model definitions & loading
│   ├── ⚙️ config.py                # Configuration settings
│   ├── 📦 requirements.txt         # Dependencies
│   └── 📘 ReadMe.md                # Module-specific documentation

├── 📂 data/                         # Dataset info & references
│   └── data.md

├── 📄 NutriVision – AI Food Analyzer (Problem Statement).pdf
└── 📘 README.md                     # Main project documentation                     
```

### Key Source Files

| File | Role |
|---|---|
| `app.py` | Gradio two-tab UI; streaming pipeline callbacks; session management; example gallery |
| `pipeline.py` | All ML logic: SAM3 segmentation, coin scale, ConvNeXtV2 classification, PCA geometry, LLM weight estimation, nutrition scaling |
| `models.py` | Lazy singleton loader for SAM3 and ConvNeXtV2 — loads once, caches for all Gradio sessions |
| `config.py` | Single source of truth for all thresholds, paths, and prompt strings |
| `food_nutrition.json` | 11 nutrients per 100g for each of 79 Indian food classes |
| `food_density.json` | Food-specific bulk densities (g/cm³) with source and basis per entry |

---

## Configuration

```import os

# ── Paths ──────────────────────────────────────────────────────────────────
# Place your model checkpoint and nutrition JSON in the same folder as app.py
# or set these env vars before running.
CKPT_PATH = (
    "/teamspace/studios/this_studio/nutrivision/files_models/best_convnextv2_tiny.pt"
)
NUTRITION_PATH = (
    "/teamspace/studios/this_studio/nutrivision/files_models/food_nutrition.json"
)
SAVE_DIR = "/teamspace/studios/this_studio/nutrivision/SAVE_DIR"
DENSITY_PATH = (
    "/teamspace/studios/this_studio/nutrivision/files_models/food_density.json"
)


# HuggingFace token (required to download facebook/sam3 if gated)
HF_TOKEN = os.environ.get("HF_TOKEN", "")
if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN

# ── ConvNeXtV2 threshold ───────────────────────────────────────────────────
CONVNEXT_CONF_THRESH = 0.40

# ── SAM3 thresholds ────────────────────────────────────────────────────────
CONF_THRESH = 0.60
IOU_THRESH = 0.40
CONT_THRESH = 0.25

# ── Coin (RBI ₹10 coin) ───────────────────────────────────────────────────
COIN_DIAMETER_CM = 2.7
COIN_CONF_THRESH = 0.50

# ── LLM (Ollama Cloud via OpenAI-compatible endpoint) ─────────────────────
OLLAMA_API_KEY = os.environ.get("OLLAMA", "")
OLLAMA_BASE_URL = "https://ollama.com/v1"
OLLAMA_MODEL = "qwen3.5:397b-cloud"


# ── SAM3 prompt strings ────────────────────────────────────────────────────
PROMPT_1 = "food and its bowl"
PROMPT_2 = "drink and its glass"
PROMPT_3 = "food"
PROMPT_COIN = "coin"

```

---


## Dependencies

```
# ── Deep Learning ─────────────────────────────────────────────────────────
torch==2.11.0
torchvision==0.26.0
timm==1.0.26
transformers==5.5.1

# ── Computer Vision / Image Processing ────────────────────────────────────
albumentations==2.0.8
opencv-python-headless==4.13.0.92
pillow==10.4.0

# ── ML / Math ─────────────────────────────────────────────────────────────
numpy==2.4.4
scikit-learn==1.8.0

# ── LLM / LangChain ───────────────────────────────────────────────────────
langchain-core==1.2.28
langchain-openai==1.1.12
openai==2.31.0

# ── Data / Plotting ───────────────────────────────────────────────────────
pandas==3.0.2
matplotlib==3.10.8

# ── Gradio UI ─────────────────────────────────────────────────────────────
gradio==6.11.0

# ── Pydantic (used in pipeline for output parsing) ────────────────────────
pydantic==2.12.5

# ── HuggingFace Hub (model download, SAM3) ────────────────────────────────
huggingface_hub==1.9.2
gdown
```

Install via:

```bash
pip install -r requirements.txt
```

---

## Tech Stack

Python · PyTorch · timm · HuggingFace SAM3 · Gradio · LangChain · Ollama LLM · Lightning AI

## Team

**Group 2 · Data Science & AI Lab · IIT Madras**

Sahil Raj · Sahil Sharma · Aman Mani Tiwari · Samreen Fathima · Tasneem Shahnawaz

---

