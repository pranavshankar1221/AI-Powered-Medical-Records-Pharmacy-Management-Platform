"""
MedTrack Configuration
Centralised settings loaded from environment variables with sensible defaults.
"""

import os
os.environ["USE_TF"] = "OFF"
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FAISS_DIR = DATA_DIR / "faiss_index"
QR_DIR = DATA_DIR / "qr_codes"
KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge_base" / "medicines.json"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
FAISS_DIR.mkdir(exist_ok=True)
QR_DIR.mkdir(exist_ok=True)

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'medtrack.db'}")

# ── Flask ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "medtrack-dev-secret-key-change-in-prod")
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
HOST = os.getenv("FLASK_HOST", "0.0.0.0")
PORT = int(os.getenv("FLASK_PORT", "5000"))

# ── Gemini API (for RAG chatbot) ─────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ── RAG Pipeline ─────────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_MAX_CONTEXT_LENGTH = int(os.getenv("RAG_MAX_CONTEXT_LENGTH", "3000"))

# ── Alert Thresholds ─────────────────────────────────────────────────────────
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "10"))
EXPIRY_WARNING_DAYS = int(os.getenv("EXPIRY_WARNING_DAYS", "30"))

# ── QR Code ──────────────────────────────────────────────────────────────────
QR_HMAC_SECRET = os.getenv("QR_HMAC_SECRET", "medtrack-qr-hmac-secret")
PHARMACY_NAME = os.getenv("PHARMACY_NAME", "MedTrack Demo Pharmacy")

# ── MLflow ───────────────────────────────────────────────────────────────────
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", f"file:///{DATA_DIR / 'mlruns'}")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "medtrack-rag")
