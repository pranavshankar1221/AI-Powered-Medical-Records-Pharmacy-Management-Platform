"""
MEDIQR MLOPS - Backend Configuration
Centralised settings via pydantic-settings with environment variable support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
QR_DIR = DATA_DIR / "qr_codes"
MLRUNS_DIR = DATA_DIR / "mlruns"
METRICS_DIR = DATA_DIR / "metrics"
RAW_DATA_DIR = DATA_DIR / "raw"

# Ensure directories exist
for d in [DATA_DIR, MODELS_DIR, QR_DIR, MLRUNS_DIR, METRICS_DIR, RAW_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://mediqr_user:mediqr_pass_2024@localhost:3306/mediqr_db"
)

# ── JWT ──────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "mediqr-dev-secret-change-in-prod-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ── Server ───────────────────────────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("ENVIRONMENT", "development") == "development"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ── Gemini API ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ── MLflow ───────────────────────────────────────────────────────────────────
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", f"file:///{MLRUNS_DIR}")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "mediqr-models")

# ── Alert Thresholds ─────────────────────────────────────────────────────────
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "10"))
EXPIRY_WARNING_DAYS = int(os.getenv("EXPIRY_WARNING_DAYS", "30"))

# ── QR Code ──────────────────────────────────────────────────────────────────
QR_HMAC_SECRET = os.getenv("QR_HMAC_SECRET", "mediqr-qr-hmac-secret")
PHARMACY_NAME = os.getenv("PHARMACY_NAME", "MEDIQR Demo Pharmacy")

# ── CORS ─────────────────────────────────────────────────────────────────────
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:80").split(",")
