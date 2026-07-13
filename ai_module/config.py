"""
AI Module Configuration
Centralised settings for local model training and experiment tracking.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
METRICS_DIR = DATA_DIR / "metrics"

# Ensure directories exist
for d in [DATA_DIR, MODELS_DIR, METRICS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── MLflow Tracking ──────────────────────────────────────────────────────────
MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI", 
    f"file:///{DATA_DIR / 'mlruns'}"
)
MLFLOW_EXPERIMENT_NAME = os.getenv(
    "MLFLOW_EXPERIMENT_NAME", 
    "mediqr-models"
)
