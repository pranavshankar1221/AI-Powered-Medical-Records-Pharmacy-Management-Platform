import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
FAISS_DIR = DATA_DIR / "faiss_index"
QR_DIR = DATA_DIR / "qr_codes"

DATA_DIR.mkdir(parents=True, exist_ok=True)
FAISS_DIR.mkdir(parents=True, exist_ok=True)
QR_DIR.mkdir(parents=True, exist_ok=True)

# DATABASE
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'medtrack.db'}"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

# FLASK
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "medtrack-dev-secret-key"
)

HOST = os.getenv("HOST", "0.0.0.0")

PORT = int(
    os.getenv("PORT", "5000")
)

DEBUG = False

# GEMINI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.0-flash"
)

# RAG
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2"
)

RAG_TOP_K = int(
    os.getenv("RAG_TOP_K", "5")
)

RAG_MAX_CONTEXT_LENGTH = int(
    os.getenv("RAG_MAX_CONTEXT_LENGTH", "3000")
)

# ALERTS
LOW_STOCK_THRESHOLD = int(
    os.getenv("LOW_STOCK_THRESHOLD", "10")
)

EXPIRY_WARNING_DAYS = int(
    os.getenv("EXPIRY_WARNING_DAYS", "30")
)

# QR
QR_HMAC_SECRET = os.getenv(
    "QR_HMAC_SECRET",
    "medtrack-qr-hmac-secret"
)

PHARMACY_NAME = os.getenv(
    "PHARMACY_NAME",
    "MedTrack Demo Pharmacy"
)

# MLFLOW
MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    f"file:///{DATA_DIR / 'mlruns'}"
)

MLFLOW_EXPERIMENT_NAME = os.getenv(
    "MLFLOW_EXPERIMENT_NAME",
    "medtrack-rag"
)