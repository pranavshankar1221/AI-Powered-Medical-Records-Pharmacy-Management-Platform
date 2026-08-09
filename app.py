


import os
import sys
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS


# ============================================================================
# PROJECT PATHS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent

AI_MODULE_DIR = BASE_DIR / "ai_module"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FLASK_STATIC_DIR = BASE_DIR / "static"


# ============================================================================
# PYTHON IMPORT PATH
# ============================================================================

# Your database/, routes/, services/, mlops/ folders are
# located directly in the project root.

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Add AI module if it exists.

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


# MLOps monitoring

try:
    from mlops.monitor import (
        get_drift_metrics,
        get_inference_logs,
    )

    MLOPS_AVAILABLE = True

except ImportError as exc:
    print(f"[WARNING] MLOps module unavailable: {exc}")

    get_drift_metrics = None
    get_inference_logs = None

    MLOPS_AVAILABLE = False


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

    print(
        f"[WARNING] Database initialization failed: {exc}"
    )


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
# MLOPS MONITORING PAGE
# ============================================================================

@app.route("/monitoring", methods=["GET"])
def monitoring_page():
    """
    Serve the React application for the monitoring route.
    """

    return serve_react_app()


# ============================================================================
# MLOPS API
# ============================================================================

@app.route("/api/mlops/metrics", methods=["GET"])
def get_monitoring_metrics():
    """
    Return drift and inference monitoring metrics.
    """

    try:

        if not MLOPS_AVAILABLE:

            return jsonify(
                {
                    "metrics": {},
                    "logs": [],
                    "warning": "MLOps monitoring module unavailable.",
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

        print(
            f"[ERROR] MLOps metrics failed: {exc}"
        )

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

    The Dockerfile builds the React application using:

        npm run build

    which creates:

        frontend/dist/
    """

    index_file = FRONTEND_DIST / "index.html"

    if not index_file.exists():

        print(
            f"[ERROR] React build not found: {index_file}"
        )

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
# HOME PAGE
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

    If the requested file exists inside frontend/dist,
    serve it directly.

    Otherwise return index.html so React Router can
    handle the client-side route.
    """

    # ------------------------------------------------------------------------
    # API routes must never be intercepted by React
    # ------------------------------------------------------------------------

    if path.startswith("api/"):

        return jsonify(
            {
                "error": "API endpoint not found",
                "path": f"/{path}",
            }
        ), 404

    # ------------------------------------------------------------------------
    # Flask static files
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
    # React/Vite static files
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

    Render does not use this function when Gunicorn is used.
    """

    host = os.getenv(
        "HOST",
        getattr(config, "HOST", "0.0.0.0"),
    )

    # Render provides PORT automatically.
    # Locally defaults to config.PORT / 5000.

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
    # Load FAISS / RAG index
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
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":

    start_local_server()