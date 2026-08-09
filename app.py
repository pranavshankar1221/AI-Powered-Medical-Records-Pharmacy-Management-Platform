"""
MedTrack - Main Flask Application

Project structure:

PROJECT/
├── app.py
├── config.py
├── requirements.txt
├── Dockerfile
├── frontend/
│   └── dist/
├── backend/
│   ├── database/
│   ├── routes/
│   ├── services/
│   ├── schemas/
│   ├── middleware/
│   └── utils/
├── ai_module/
├── mlops/
├── data/
└── knowledge_base/
"""

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS


# ============================================================================
# PROJECT PATHS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent

BACKEND_DIR = BASE_DIR / "backend"
AI_MODULE_DIR = BASE_DIR / "ai_module"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FLASK_STATIC_DIR = BASE_DIR / "static"


# ============================================================================
# PYTHON IMPORT PATHS
# ============================================================================

# Root project directory
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Backend directory
# This allows:
# from database.db import ...
# from routes.inventory import ...
# etc.
if BACKEND_DIR.exists() and str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# AI module
if AI_MODULE_DIR.exists() and str(AI_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_MODULE_DIR))


# ============================================================================
# APPLICATION IMPORTS
# ============================================================================

import config

from database.db import init_db

from routes.inventory import inventory_bp
from routes.billing import billing_bp
from routes.patient import patient_bp


# MLOps is in the project root in your repository
try:
    from mlops.monitor import (
        get_drift_metrics,
        get_inference_logs,
    )
except ImportError:
    get_drift_metrics = None
    get_inference_logs = None


# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(
    __name__,
    static_folder=str(FLASK_STATIC_DIR),
    static_url_path="/static",
)

app.secret_key = config.SECRET_KEY


# ============================================================================
# CORS
# ============================================================================

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*"
        }
    },
)


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

try:
    init_db()
    print("[OK] Database initialized successfully.")

except Exception as exc:
    print(f"[WARNING] Database initialization failed: {exc}")


# ============================================================================
# REGISTER BLUEPRINTS
# ============================================================================

app.register_blueprint(inventory_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(patient_bp)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for Render.
    """

    return jsonify(
        {
            "status": "healthy",
            "application": "MedTrack",
        }
    )


# ============================================================================
# MLOPS MONITORING
# ============================================================================

@app.route("/monitoring", methods=["GET"])
def monitoring_page():
    """
    Monitoring page.

    React Router can handle the frontend route.
    """

    return serve_react_app()


@app.route("/api/mlops/metrics", methods=["GET"])
def get_monitoring_metrics():
    """
    Return drift and inference monitoring metrics.
    """

    try:

        if get_drift_metrics is None or get_inference_logs is None:
            return jsonify(
                {
                    "metrics": {},
                    "logs": [],
                    "warning": "MLOps monitoring module is unavailable.",
                }
            )

        metrics = get_drift_metrics()
        recent_logs = get_inference_logs(15)

        return jsonify(
            {
                "metrics": metrics,
                "logs": recent_logs,
            }
        )

    except Exception as exc:

        return jsonify(
            {
                "error": "Unable to retrieve monitoring metrics",
                "details": str(exc),
            }
        ), 500


# ============================================================================
# REACT FRONTEND
# ============================================================================

def serve_react_app():
    """
    Serve the production React/Vite application.

    Docker builds the frontend using:

        npm run build

    which creates:

        frontend/dist/
    """

    index_file = FRONTEND_DIST / "index.html"

    if not index_file.exists():

        return jsonify(
            {
                "error": "React frontend build not found.",
                "expected_path": str(index_file),
            }
        ), 500

    return send_from_directory(
        str(FRONTEND_DIST),
        "index.html",
    )


# ============================================================================
# HOME
# ============================================================================

@app.route("/", methods=["GET"])
def home():
    """
    Serve React application.
    """

    return serve_react_app()


# ============================================================================
# REACT ROUTER / STATIC FILE FALLBACK
# ============================================================================

@app.route("/<path:path>", methods=["GET"])
def react_routes(path):
    """
    Serve React/Vite static files.

    If a requested file exists in frontend/dist,
    serve it.

    Otherwise return index.html so React Router
    can handle the client-side route.
    """

    # ------------------------------------------------------------------------
    # Never intercept API routes
    # ------------------------------------------------------------------------

    if path.startswith("api/"):

        return jsonify(
            {
                "error": "API endpoint not found",
                "path": f"/{path}",
            }
        ), 404

    # ------------------------------------------------------------------------
    # Static files
    # ------------------------------------------------------------------------

    if path.startswith("static/"):

        static_path = path[len("static/"):]

        static_file = FLASK_STATIC_DIR / static_path

        if static_file.exists() and static_file.is_file():

            return send_from_directory(
                str(FLASK_STATIC_DIR),
                static_path,
            )

        return jsonify(
            {
                "error": "Static file not found",
                "path": f"/{path}",
            }
        ), 404

    # ------------------------------------------------------------------------
    # React/Vite static file
    # ------------------------------------------------------------------------

    requested_file = FRONTEND_DIST / path

    if requested_file.exists() and requested_file.is_file():

        return send_from_directory(
            str(FRONTEND_DIST),
            path,
        )

    # ------------------------------------------------------------------------
    # React Router fallback
    # ------------------------------------------------------------------------

    return serve_react_app()


# ============================================================================
# LOCAL DEVELOPMENT
# ============================================================================

def start_local_server():
    """
    Start Flask development server locally.
    """

    host = getattr(
        config,
        "HOST",
        os.getenv("HOST", "0.0.0.0"),
    )

    # Render provides PORT through environment variables.
    port = int(
        os.getenv(
            "PORT",
            getattr(config, "PORT", 5000),
        )
    )

    debug = getattr(
        config,
        "DEBUG",
        False,
    )

    # ------------------------------------------------------------------------
    # Try loading FAISS / RAG index
    # ------------------------------------------------------------------------

    try:

        from services.rag_engine import ensure_index_loaded

        if ensure_index_loaded():

            print(
                "[OK] FAISS index loaded successfully "
                "into RAG Engine."
            )

        else:

            print(
                "[WARNING] FAISS index files not found "
                "in data/faiss_index/."
            )

    except Exception as exc:

        print(
            f"[WARNING] RAG engine could not be initialized: {exc}"
        )

    # ------------------------------------------------------------------------
    # Start Flask
    # ------------------------------------------------------------------------

    print(
        f"MedTrack App starting on "
        f"http://{host}:{port}"
    )

    app.run(
        host=host,
        port=port,
        debug=debug,
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    start_local_server()