import os

# ── Paths ──────────────────────────────────────────────────────────────────
# Place your model checkpoint and nutrition JSON in the same folder as app.py
# or set these env vars before running.
CKPT_PATH = (
    "/teamspace/studios/this_studio/nutrivision_codes/files_models/best_convnextv2_tiny.pt"
)
NUTRITION_PATH = (
    "/teamspace/studios/this_studio/nutrivision_codes/files_models/food_nutrition.json"
)
SAVE_DIR = "/teamspace/studios/this_studio/nutrivision_codes/SAVE_DIR"
DENSITY_PATH = (
    "/teamspace/studios/this_studio/nutrivision_codes/files_models/food_density.json"
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

# ── Nutrition columns ──────────────────────────────────────────────────────
NUTRIENT_COLS = [
    "calories_kcal",
    "carbohydrates_g",
    "protein_g",
    "fats_g",
    "free_sugar_g",
    "fibre_g",
    "sodium_mg",
    "calcium_mg",
    "iron_mg",
    "vitamin_c_mg",
    "folate_ug",
]
NUTRIENT_LABELS = [
    "Calories (kcal)",
    "Carbs (g)",
    "Protein (g)",
    "Fat (g)",
    "Free Sugar (g)",
    "Fibre (g)",
    "Sodium (mg)",
    "Calcium (mg)",
    "Iron (mg)",
    "Vitamin C (mg)",
    "Folate (µg)",
]
