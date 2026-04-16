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

## **System Architecture**
```
User Input (Image)
        │
        ▼
Gradio Interface (app.py)
        │
        ▼
Inference Pipeline (pipeline.py)
        │
        ▼
Model Loader (models.py)
        │
        ▼
Prediction (Food Class)
        │
        ▼
Nutrition Mapping (JSON files)
        │
        ▼
Final Output (Calories, Nutrition Info)
```

## **Getting started**

### 1. Prerequisites
Ensure the following before setup:

Python 3.9 or higher
Lightning AI environment (for deployment)
Access to model weights (via Google Drive link)
API credentials:
Hugging Face Token
Ollama API Key
### 2. Clone the repo on root folder
```
git clone --filter=blob:none --sparse https://github.com/23f3001764/Group-2-DS-and-AI-Lab-Project.git
cd Group-2-DS-and-AI-Lab-Project
git sparse-checkout set nutrivision_codes
cd nutrivision_codes
```
### 3. Environment Configuration
Set the following environment variables in your platform in global api (Lightning AI):
https://lightning.ai/<profile_id>/home?settings=secrets 
```
HF_TOKEN=<your_huggingface_token>
OLLAMA_API_KEY=<your_ollama_api_key>
```
### 4. Installation
Install all required dependencies:
```
pip install -r requirements.txt
```
### 5. Activate the GPU T4
GPU cost : 0.14$ per hour
### 6. Model Setup
1. Navigate to:
```files_models/model_py.txt```
3. Download the model weights from the provided Google Drive link.
```
cd files_models
gdown https://drive.google.com/file/d/1w8PQt-7Ofn4pjTUUC2YqwIxEicy2Zxhe/view?usp=sharing
cd ..
```
4. Place the downloaded weights inside:
```files_models/```
The application will not run without the model weights.
you can correct all the paths on config.py if you face any error

### 7. Running the Application
Execute the application using:
```
python app.py
```
the you can acess the web app on network url showing in the terminal
### 8. Deployment (Lightning AI)
First download & Install the gradio by clicking + sign in the right hand tool bar and then opening web apps and after installing it open the gradio
and give the port 7860 and in running command python app.py and choose the T4 GPU

Configure the deployment with:

Framework: Gradio
Mode: Serverless
Port: 7860

Once deployed, the application will be accessible via a public endpoint.

## Dependencies used

The complete list of dependencies used for the final run is:

```python
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

## Repository Structure

```python
main/
│── Archive/Deprecated_Experiments/...
│
├── Notebooks/
│   ├── EDA/
│   │   ├── Khana_Dataset_EDA.ipynb
│   │
│   ├── Model_Training/
│   │   ├── ConvNeXtV2_Training.ipynb
│   │
│   ├── Model_Evaluation/
│   │   └── Model_Pipeline_Evaluation.ipynb
│   │
│   └── Weight_PCA/
│       └── Weight_PCA_Pipeline.ipynb
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
├── nutrivision_codes/
│   └── files_models/
│   │   ├── food_density.json        # Density values for portion estimation
│   │   ├── food_nutrition.json      # Nutritional database
│   │   └── model_py.txt             # Contains link to model weights
│   │
│   ├── test_images/..               # Sample inputs for testing
│   │
│   ├── app.py                       # Entry point (Gradio UI)
│   ├── config.py                    # Configuration and constants
│   ├── models.py                    # Model loading logic
│   ├── pipeline.py                  # Core inference pipeline
│   ├── requirements.txt             # Dependencies
│   └── README.md
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

## Module Description
- app.py
Main application entry point
Builds and launches the Gradio interface
Handles user input and displays output
- pipeline.py
Core logic for inference
Handles:
Image preprocessing
Model prediction
Post-processing
- models.py
Loads trained model and weights
Ensures the model is ready for inference
- config.py
Stores:
File paths
Constants
Environment configurations
- JSON Files
food_nutrition.json
→ Maps food items to nutritional values
food_density.json
→ Supports portion/density-based calculations

- **Repository Link:**  
  https://github.com/23f3001764/Group-2-DS-and-AI-Lab-Project.git  

- **Reviewed By:**

  - **Aman Mani Tiwari**  
    <img src="../Images/aman.jpeg" width="150"/>

  - **Sahil Raj**  
    <img src="../Images/sahil_raj.jpeg" width="150"/>

  - **Sahil Sharma**  
    <img src="../Images/sahil.jpeg" width="150"/>

  - **Samreen Fathima**  
    <img src="../Images/me.jpeg" width="150"/>

  - **Tasneem Shahnawaz**  
    <img src="../Images/tasneem.jpeg" width="150"/>

