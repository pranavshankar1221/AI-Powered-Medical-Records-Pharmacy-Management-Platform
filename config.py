"""
MedTrack Configuration
Centralized settings loaded from environment variables.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================================
# ENVIRONMENT
# ============================================================================

load_dotenv()

# Disable TensorFlow if not required
os.environ.setdefault("USE_TF", "OFF")


# ============================================================================
# PROJECT PATHS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
FAISS_DIR = DATA_DIR / "faiss_index"
QR_DIR = DATA_DIR / "qr_codes"

KNOWLEDGE_BASE_PATH = (
    BASE_DIR / "knowledge_base" / "medicines.json"
)


# Create required directories

DATA_DIR.mkdir(parents=True, exist_ok=True)
FAISS_DIR.mkdir(parents=True, exist_ok=True)
QR_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# DATABASE
# ============================================================================

# Render PostgreSQL should provide DATABASE_URL
#
# Local development falls back to SQLite.

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'medtrack.db'}"


# Render/Heroku-style postgres:// URLs can be normalized
# for SQLAlchemy.

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1,
    )


# ============================================================================
# FLASK
# ============================================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "medtrack-dev-secret-key-change-in-prod",
)

DEBUG = (
    os.getenv(
        "FLASK_DEBUG",
        "false",
    ).lower()
    == "true"
)

HOST = os.getenv(
    "HOST",
    "0.0.0.0",
)

PORT = int(
    os.getenv(
        "PORT",
        os.getenv(
            "FLASK_PORT",
            "5000",
        ),
    )
)


# ============================================================================
# GEMINI
# ============================================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "",
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.0-flash",
)


# ============================================================================
# RAG
# ============================================================================

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2",
)

RAG_TOP_K = int(
    os.getenv(
        "RAG_TOP_K",
        "5",
    )
)

RAG_MAX_CONTEXT_LENGTH = int(
    os.getenv(
        "RAG_MAX_CONTEXT_LENGTH",
        "3000",
    )
)


# ============================================================================
# ALERT THRESHOLDS
# ============================================================================

LOW_STOCK_THRESHOLD = int(
    os.getenv(
        "LOW_STOCK_THRESHOLD",
        "10",
    )
)

EXPIRY_WARNING_DAYS = int(
    os.getenv(
        "EXPIRY_WARNING_DAYS",
        "30",
    )
)


# ============================================================================
# QR CODE
# ============================================================================

QR_HMAC_SECRET = os.getenv(
    "QR_HMAC_SECRET",
    "medtrack-qr-hmac-secret",
)

PHARMACY_NAME = os.getenv(
    "PHARMACY_NAME",
    "MedTrack Demo Pharmacy",
)


# ============================================================================
# NEO4J
# ============================================================================

NEO4J_URI = os.getenv(
    "NEO4J_URI",
    "bolt://localhost:7687",
)

NEO4J_USER = os.getenv(
    "NEO4J_USER",
    "neo4j",
)

NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD",
    "",
)


# ============================================================================
# MLFLOW
# ============================================================================

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    f"file:///{DATA_DIR / 'mlruns'}",
)

MLFLOW_EXPERIMENT_NAME = os.getenv(
    "MLFLOW_EXPERIMENT_NAME",
    "medtrack-rag",
)


# ============================================================================
# STARTUP INFORMATION
# ============================================================================

print("=" * 70)
print("MedTrack Configuration")
print("=" * 70)

print(
    f"Database: "
    f"{'PostgreSQL' if DATABASE_URL.startswith('postgresql') else 'SQLite'}"
)

print(f"Host: {HOST}")
print(f"Port: {PORT}")
print(f"FAISS directory: {FAISS_DIR}")

print("=" * 70)