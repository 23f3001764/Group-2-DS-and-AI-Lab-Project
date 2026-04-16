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

### Prerequisites
Ensure the following before setup:

Python 3.9 or higher
Lightning AI environment (for deployment)
Access to model weights (via Google Drive link)
API credentials:
Hugging Face Token
Ollama API Key

### Environment Configuration
Set the following environment variables in your platform (Lightning AI):
```
HF_TOKEN=<your_huggingface_token>
OLLAMA_API_KEY=<your_ollama_api_key>
```
### Installation
Install all required dependencies:
```
pip install -r requirements.txt
```
### Model Setup
1. Navigate to:
```files_models/model_py.txt```
3. Download the model weights from the provided Google Drive link.
4. Place the downloaded weights inside:
```files_models/```
The application will not run correctly without the model weights.

### Running the Application
Execute the application using:
```python app.py```

### Deployment (Lightning AI)

Configure the deployment with:

Framework: Gradio
Mode: Serverless
Port: 7860

Once deployed, the application will be accessible via a public endpoint.

## Dependencies used

The complete list of dependencies used for the final run is:

```python
torch==2.2.2
torchvision==0.17.2
timm==0.9.12
transformers==4.40.2

albumentations==1.4.4
opencv-python-headless==4.9.0.80
pillow==10.3.0

numpy==1.26.4
scikit-learn==1.4.2

langchain-core==0.2.5
langchain-openai==0.1.7
openai==1.30.1
pandas==2.2.2
matplotlib==3.8.4
gradio==4.31.5

pydantic==2.7.1
huggingface_hub==0.23.0
gdown==5.1.0
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

## 8. Module Description
### 8.1 app.py
Main application entry point
Builds and launches the Gradio interface
Handles user input and displays output
### 8.2 pipeline.py
Core logic for inference
Handles:
Image preprocessing
Model prediction
Post-processing
### 8.3 models.py
Loads trained model and weights
Ensures the model is ready for inference
### 8.4 config.py
Stores:
File paths
Constants
Environment configurations
### 8.5 JSON Files
food_nutrition.json
→ Maps food items to nutritional values
food_density.json
→ Supports portion/density-based calculations
