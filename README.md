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
3. Classifies items across 80 Indian food categories (97.92% Top-1 accuracy)
4. Estimates real-world portion weight using PCA geometry + food-specific density
5. Returns a full macro/micronutrient breakdown and personalised dietary suggestions

## Pipeline

```
Input Image
  → SAM3 Segmentation          (pixel masks for food, container, coin)
  → Coin Scale Extraction      (₹10 coin → px/cm calibration factor)
  → ConvNeXtV2 Classification  (80 Indian food classes)
  → PCA Geometry               (rotation-invariant major/minor axes)
  → LLM Weight Estimation      (geometry model × density-enforced lookup)
  → Nutrition Scaling          (per-100g values × estimated weight)
  → Output                     (annotated image + nutrition table + LLM reasoning)
```

The pipeline is a **streaming generator** — Gradio streams progress after each of 5 stages, so you see live step-by-step feedback rather than waiting for the full result.

---

## Quick Start

### Prerequisites

- Google Colab (GPU recommended) **or** a local machine with CUDA
- Hugging Face account with [SAM3 access](https://huggingface.co/facebook/sam3) approved
- OpenRouter API key (for LLM weight reasoning)

### 1. Open the Notebook

Upload or open the main notebook in Google Colab, then enable GPU:

```
Runtime → Change runtime type → GPU
```

### 2. Download Models & Sample Image

Run the setup cell (auto-executed at notebook start):

```python
!pip install -q gdown

# Download ConvNeXtV2-Tiny checkpoint (~110 MB)
!gdown https://drive.google.com/uc?id=1dgX5MFNYdZcckuty7XqjqlfpplGCbjLx -O best_convnextv2_tiny.pt

# Download sample image
!gdown https://drive.google.com/uc?id=1TWZT2X1oVqhnK7p7BFyrmRTi08xFzXtw -O sample.jpg

CKPT_PATH  = "/content/best_convnextv2_tiny.pt"
IMAGE_PATH = "/content/sample.jpg"
```

> **Note:** The ConvNeXtV2 model is hosted externally due to GitHub's file size limits.

### 3. Set API Keys

```python
import os

os.environ["OPENROUTER_API_KEY"] = "your_openrouter_key"   # LLM weight reasoning
os.environ["HF_TOKEN"]           = "your_huggingface_token" # SAM3 (gated model)
```

> If `HF_TOKEN` is missing or SAM3 access is not approved, segmentation will fail at Step 1.
> If `OPENROUTER_API_KEY` is missing, the LLM weight step is skipped — the core pipeline still runs.

### 4. Run All Cells

Execute cells in order:

1. Setup (installs dependencies, downloads model + image)
2. Load SAM3 model
3. Load ConvNeXtV2 model
4. Run segmentation
5. Run classification
6. Compute PCA + scale
7. Run LLM estimation

### 5. Use the Web App

For the deployed Gradio interface:

- Upload a photo of your meal with a **₹10 coin lying flat** in frame
- Click **Analyse**
- Watch the 5-step progress checklist stream live
- View the annotated image, nutrition table, and LLM weight reasoning

## Gradio Interface

![Report](Report/Images/ds1.jpg)

### Gradio Output Interface

![Report](Report/Images/ds4.jpg)

---

## Repository Structure

```
main/
│
├── Notebooks/
│   ├── EDA/
│   │   ├── Image_Dataset_EDA.ipynb
│   │   ├── Khana_Dataset_EDA.ipynb
│   │   └── Nutrition_Values_Dataset_EDA.ipynb
│   │
│   ├── HyperParameter/
│   │   └── Convnextv2_Tuning.ipynb
│   │
│   ├── Model_Training/
│   │   ├── ConvNeXtV2_Training.ipynb
│   │   ├── EfficientNetV2s_Training.ipynb
│   │   ├── MLP_Training.ipynb
│   │   ├── MobileNetV2_Training.ipynb
│   │   ├── YOLO_MLP_Training.ipynb
│   │   ├── YOLOv12s_Initial_Training.ipynb
│   │   ├── YOLOv12s_Main_Training.ipynb
│   │   ├── YOLOv12s_Final_Training.ipynb
│   │   ├── YOLOv26_Training.ipynb
│   │   └── training_history.csv
│   │
│   ├── Model_Evaluation/
│   │   └── Model_Pipeline_Evaluation.ipynb
│   │
│   └── Weight_PCA/
│       └── Weight_PCA_Pipeline.ipynb
│
├── Preprocessing/
│   ├── Data_Cleaning.ipynb
│   └── Data_Preprocessing.ipynb
│
├── Presentation/
│   ├── Milestone_1.pdf  →  Milestone_5.pdf
│
├── Report/
│   ├── Contribution/
│   ├── Images/
│   └── Milestone_1_Report.md  →  Milestone_5_Report.pdf
│
├── data/
│   └── data.md
│
├── app.py                  ← Gradio UI (517 lines)
├── pipeline.py             ← Core ML pipeline (839 lines)
├── models.py               ← Lazy model loader (SAM3 + ConvNeXtV2)
├── config.py               ← All paths, thresholds, prompts, LLM settings
├── food_nutrition.json     ← Per-100g nutritional values for 80 foods
├── food_density.json       ← Apparent bulk density (g/cm³) for 80 foods
├── requirements.txt
├── .gitignore
└── NutriVision – AI Food Analyzer.pdf
```

### Key Source Files

| File | Role |
|---|---|
| `app.py` | Gradio two-tab UI; streaming pipeline callbacks; session management; example gallery |
| `pipeline.py` | All ML logic: SAM3 segmentation, coin scale, ConvNeXtV2 classification, PCA geometry, LLM weight estimation, nutrition scaling |
| `models.py` | Lazy singleton loader for SAM3 and ConvNeXtV2 — loads once, caches for all Gradio sessions |
| `config.py` | Single source of truth for all thresholds, paths, and prompt strings |
| `food_nutrition.json` | 11 nutrients per 100g for each of 80 Indian food classes |
| `food_density.json` | Food-specific bulk densities (g/cm³) with source and basis per entry |

---

## Configuration

All runtime parameters live in `config.py` — never hard-coded in `pipeline.py`:

```python
CKPT_PATH             = '.../best_convnextv2_tiny.pt'
NUTRITION_PATH        = '.../food_nutrition.json'
DENSITY_PATH          = '.../food_density.json'

CONVNEXT_CONF_THRESH  = 0.40   # classifier min confidence (below → reject)
CONF_THRESH           = 0.60   # SAM3 food segment confidence
IOU_THRESH            = 0.40   # mask merge IoU threshold
CONT_THRESH           = 0.25   # containment threshold (food-only vs container)

COIN_DIAMETER_CM      = 2.7    # RBI ₹10 coin known diameter
COIN_CONF_THRESH      = 0.50   # SAM3 coin detection confidence

OLLAMA_MODEL          = 'qwen3.5:397b-cloud'

PROMPT_1              = 'food and its bowl'
PROMPT_2              = 'drink and its glass'
PROMPT_3              = 'food'
PROMPT_COIN           = 'coin'
```

---

## Data Files

### `food_nutrition.json`

Per-100g values for all 80 supported Indian foods, with 11 nutrient fields:

```
calories_kcal · carbohydrates_g · protein_g · fats_g · free_sugar_g
fibre_g · sodium_mg · calcium_mg · iron_mg · vitamin_c_mg · folate_ug
```

### `food_density.json`

Apparent bulk density (g/cm³) as-served, with source and basis per entry. Published values (e.g. idli: 0.53 g/cm³ from PMC/Springer) are flagged separately from engineering inference values.

---

## Dependencies

```
torch · torchvision · timm · transformers
opencv-python · pillow · numpy · albumentations
matplotlib · scikit-learn
langchain · langchain-openrouter · openai
gradio · pydantic · huggingface_hub
gdown · pandas
```

Install via:

```bash
pip install -r requirements.txt
```

---

## Image Requirements

For best results:

- Place a **₹10 coin flat and clearly visible** in frame — the pipeline halts at Step 2 if no coin is detected
- Ensure food items are not heavily occluded
- Use good, even lighting
- Avoid extreme angles (overhead or top-down works best)

> ⚠️ The coin is **required** for scale calibration. Without it, the pipeline cannot estimate real-world dimensions.

---

## Team

**Group 2 · Data Science & AI Lab · IIT Madras**

Sahil Raj · Sahil Sharma · Aman Mani Tiwari · Samreen Fathima · Tasneem Shahnawaz

---

## Tech Stack

Python · PyTorch · timm · HuggingFace SAM3 · Gradio · LangChain · Ollama LLM · Lightning AI
