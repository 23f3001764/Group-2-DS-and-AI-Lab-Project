# Developer Guide

## **Introduction**

Welcome to the Developer guide for running NutriVision; an AI-powered food analysis system designed to perform nutritional analysis of food images uploaded by users and provide dietary recommendations.

The system integrates multiple components to enable:

- Food segmentation using a SAM-based model
- Food classification using ConvNeXtV2 and EfficientNetV2
- Object dimension estimation using PCA
- Volume and weight estimation via coin-based calibration
- Nutrition information retrieval
- LLM-based dietary recommendations

The project is modular and reproducible by following the steps below.

## Pipeline flow

Input Image
→ Segmentation (SAM)
→ Classification (ConvNeXtV2)
→ PCA Estimation
→ Coin Calibration
→ Volume Estimation
→ Weight Estimation
→ Nutrition Lookup
→ LLM Suggestions

## **Getting started**

### 1. Open Notebook

- Upload or open the main notebook in Google Colab
- Enable GPU:

```
Runtime → Change runtime type → GPU
```

### 2. Download the model .pt files and image files

- The ConvNeXtV2 model is hosted externally due to GitHub size limits.
- A default sample image is automatically downloaded in the notebook. You can also upload your own image inside the notebook.

```python
# ── Setup ─────────────────────────────────────────────
!pip install -q gdown

# Download model
!gdown https://drive.google.com/uc?id=1dgX5MFNYdZcckuty7XqjqlfpplGCbjLx -O best_convnextv2_tiny.pt

# Download sample image
!gdown https://drive.google.com/uc?id=1TWZT2X1oVqhnK7p7BFyrmRTi08xFzXtw -O sample.jpg

# Paths
CKPT_PATH = "/content/best_convnextv2_tiny.pt"
IMAGE_PATH = "/content/sample.jpg"

print("Setup complete")
```

### 3. API Keys

This project uses external APIs for advanced features. The placeholders need to be replaced with your actual API keys.

- OpenRouter (LLM dietary recommendations)

```python
os.environ["OPENROUTER_API_KEY"] = "your_key"
```

- Hugging Face (SAM3 Model)

```python
import os 
os.environ["HF_TOKEN"] = "your_token"
```

### 4. Run the Notebook

Run all cells in order:

1. Setup (auto download + install dependencies, models and images)
2. Load SAM3 model
3. Load ConvNeXtV2 model
4. Run segmentation
5. Run classification
6. Compute PCA + scale
7. Run LLM estimation

## Dependencies used

The complete list of dependencies used for the final run are:

```python
torch
torchvision
transformers
timm

opencv-python
pillow
numpy
albumentations

matplotlib
scikit-learn

langchain
langchain-openrouter
openai

gdown
```

## Repository Structure

```python
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
│   ├── Milestone_1.pdf
│   ├── Milestone_2.pdf
│   ├── Milestone_3.pdf
│   ├── Milestone_4.pdf
│   └── Milestone_5.pdf
│
├── Report/
│   ├── Contribution/
│   │   ├── Milestone1_Contribution.md
│   │   ├── Milestone2_Contribution.md
│   │   ├── Milestone3_Contribution.md
│   │   └── Milestone4_Contribution.md
│   │
│   ├── Images/
│   │
│   ├── Milestone_1_Report.md
│   ├── Milestone_2_Report.md
│   ├── Milestone_3_Report.md
│   ├── Milestone_4_Report.pdf
│   └── Milestone_5_Report.pdf
│
├── data/
│   └── data.md
│
├── .gitignore
│
└── NutriVision – AI Food Analyzer.pdf
```

This repository includes additional notebooks for experimentation and model development:

- EDA — dataset exploration
- Model Training — ConvNeXtV2, EfficientNetV2, YOLO
- Hyperparameter tuning
- PCA and geometry experiments

These are not required to run the final pipeline and are provided for reference.

## **Notes**

#### 1. File Paths

All paths are set for Colab:

```python
CKPT_PATH = "/content/best_convnextv2_tiny.pt"
IMAGE_PATH = "/content/sample.jpg"
```

If running locally:

- Update paths accordingly
- Ensure files exist before execution

#### 2. Hugging Face (SAM3 Access)

SAM3 is a gated model.

- Users must request access on Hugging Face
- Login is required before loading the model

If authentication fails:

- Segmentation step will fail

#### 3. API Keys

LLM-based weight estimation requires an OpenRouter API key.

- If not provided → step is skipped
- Core pipeline still runs

#### 4. GPU vs CPU Execution

- GPU is recommended for SAM3 and ConvNeXt
- On CPU:
    - Execution will be significantly slower
    - Mixed precision is automatically disable

#### 5. Image Requirements

For best results:

- Ensure food and coin are clearly visible
- Avoid heavy occlusion
- Use good lighting conditions