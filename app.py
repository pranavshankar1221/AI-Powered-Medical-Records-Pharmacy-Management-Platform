"""
app.py
Main entry point for MedTrack.

Flask backend + React/Vite frontend served from a single application.
"""

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
AI_MODULE_DIR = BASE_DIR / "ai_module"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FLASK_STATIC_DIR = BASE_DIR / "static"

# Add ai_module to Python path
if str(AI_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_MODULE_DIR))


# ---------------------------------------------------------------------------
# Application imports
# ---------------------------------------------------------------------------

import config

from database.db import init_db

from routes.inventory import inventory_bp
from routes.billing import billing_bp
from routes.patient import patient_bp

from mlops.monitor import (
    get_drift_metrics,
    get_inference_logs,
)


# ---------------------------------------------------------------------------
# Flask application
# ---------------------------------------------------------------------------

app = Flask(
    __name__,
    static_folder=str(FLASK_STATIC_DIR),
    static_url_path="/static",
)

app.secret_key = config.SECRET_KEY

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

# For deployment, you can restrict this to your Render domain.
# Keeping "*" here is useful while testing.
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*"
        }
    },
)


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

try:
    init_db()
    print("[OK] Database initialized successfully.")
except Exception as exc:
    print(f"[WARNING] Database initialization failed: {exc}")


# ---------------------------------------------------------------------------
# Register Flask Blueprints
# ---------------------------------------------------------------------------

app.register_blueprint(inventory_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(patient_bp)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Render and monitoring."""
    return jsonify(
        {
            "status": "healthy",
            "application": "MedTrack",
        }
    )


# ---------------------------------------------------------------------------
# MLOps Monitoring
# ---------------------------------------------------------------------------

@app.route("/monitoring", methods=["GET"])
def monitoring_page():
    """
    Monitoring endpoint.

    If the React frontend contains a monitoring page,
    React Router can handle the frontend route.
    """
    return serve_react_app()


@app.route("/api/mlops/metrics", methods=["GET"])
def get_monitoring_metrics():
    """Return drift and inference monitoring metrics."""

    try:
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


# ---------------------------------------------------------------------------
# React frontend
# ---------------------------------------------------------------------------

def serve_react_app():
    """
    Serve the production React/Vite application.

    React must first be built using:

        npm run build

    which creates:

        frontend/dist/
    """

    index_file = FRONTEND_DIST / "index.html"

    if not index_file.exists():
        return (
            jsonify(
                {
                    "error": "React frontend build not found.",
                    "message": (
                        "Run 'npm run build' inside the frontend directory "
                        "before starting the Flask application."
                    ),
                }
            ),
            500,
        )

    return send_from_directory(
        FRONTEND_DIST,
        "index.html",
    )


@app.route("/", methods=["GET"])
def home():
    """Serve React application."""
    return serve_react_app()


@app.route("/<path:path>", methods=["GET"])
def react_routes(path):
    """
    Serve React static files.

    If the requested file exists inside frontend/dist,
    serve it directly.

    Otherwise return index.html so React Router can
    handle client-side routes.
    """

    # -----------------------------------------------------------------------
    # Never intercept API routes
    # -----------------------------------------------------------------------

    if path.startswith("api/"):
        return jsonify(
            {
                "error": "API endpoint not found",
                "path": f"/{path}",
            }
        ), 404

    # -----------------------------------------------------------------------
    # Never intercept Flask static files
    # -----------------------------------------------------------------------

    if path.startswith("static/"):
        static_path = path[len("static/"):]

        static_file = FLASK_STATIC_DIR / static_path

        if static_file.exists() and static_file.is_file():
            return send_from_directory(
                FLASK_STATIC_DIR,
                static_path,
            )

        return jsonify(
            {
                "error": "Static file not found",
                "path": f"/{path}",
            }
        ), 404

    # -----------------------------------------------------------------------
    # Serve an actual React/Vite file
    # -----------------------------------------------------------------------

    requested_file = FRONTEND_DIST / path

    if requested_file.exists() and requested_file.is_file():

        return send_from_directory(
            FRONTEND_DIST,
            path,
        )

    # -----------------------------------------------------------------------
    # React Router fallback
    # -----------------------------------------------------------------------

    return serve_react_app()


# ---------------------------------------------------------------------------
# Local development
# ---------------------------------------------------------------------------

def start_local_server():
    """Start Flask development server locally."""

    host = getattr(
        config,
        "HOST",
        os.getenv("HOST", "0.0.0.0"),
    )

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

    # -----------------------------------------------------------------------
    # Try to load FAISS/RAG index
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Start Flask
    # -----------------------------------------------------------------------

    print(
        f"MedTrack App starting on "
        f"http://{host}:{port}"
    )

    app.run(
        host=host,
        port=port,
        debug=debug,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    start_local_server()
