import os
import sys
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS


# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(BASE_DIR))

AI_MODULE_DIR = BASE_DIR / "ai_module"

if AI_MODULE_DIR.exists():
    sys.path.insert(0, str(AI_MODULE_DIR))


# ============================================================
# CONFIG
# ============================================================

import config


# ============================================================
# DIRECTORIES
# ============================================================

FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FLASK_STATIC_DIR = BASE_DIR / "static"


# ============================================================
# DATABASE
# ============================================================

from database.db import init_db


# ============================================================
# ROUTES
# ============================================================

from routes.inventory import inventory_bp
from routes.billing import billing_bp
from routes.patient import patient_bp


# ============================================================
# MLOPS
# ============================================================

try:
    from mlops.monitor import (
        get_drift_metrics,
        get_inference_logs,
    )

    MLOPS_AVAILABLE = True

except Exception as exc:

    print(f"[WARNING] MLOps unavailable: {exc}")

    get_drift_metrics = None
    get_inference_logs = None

    MLOPS_AVAILABLE = False


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = config.SECRET_KEY


# ============================================================
# CORS
# ============================================================

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*"
        }
    }
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

try:

    init_db()

    print("[OK] PostgreSQL database initialized.")

except Exception as exc:

    print("[WARNING] Database initialization failed:")
    print(exc)


# ============================================================
# BLUEPRINTS
# ============================================================

app.register_blueprint(inventory_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(patient_bp)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health_check():

    return jsonify({
        "status": "healthy",
        "application": "MedTrack"
    })


# ============================================================
# MLOPS
# ============================================================

@app.route("/api/mlops/metrics", methods=["GET"])
def get_monitoring_metrics():

    try:

        if not MLOPS_AVAILABLE:

            return jsonify({
                "metrics": {},
                "logs": [],
                "warning": "MLOps unavailable"
            })

        metrics = get_drift_metrics()
        logs = get_inference_logs(15)

        return jsonify({
            "metrics": metrics,
            "logs": logs
        })

    except Exception as exc:

        return jsonify({
            "error": "Unable to retrieve monitoring metrics",
            "details": str(exc)
        }), 500


# ============================================================
# REACT FRONTEND
# ============================================================

def serve_react_app():

    index_file = FRONTEND_DIST / "index.html"

    if not index_file.exists():

        return jsonify({
            "error": "React frontend build not found",
            "expected": str(index_file)
        }), 500

    return send_from_directory(
        str(FRONTEND_DIST),
        "index.html"
    )


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return serve_react_app()


# ============================================================
# REACT ROUTER FALLBACK
# ============================================================

@app.route("/<path:path>", methods=["GET"])
def react_routes(path):

    # --------------------------------------------------------
    # API routes
    # --------------------------------------------------------

    if path.startswith("api/"):

        return jsonify({
            "error": "API endpoint not found",
            "path": f"/{path}"
        }), 404


    # --------------------------------------------------------
    # Flask static files
    # --------------------------------------------------------

    if path.startswith("static/"):

        static_path = path[len("static/"):]

        static_file = FLASK_STATIC_DIR / static_path

        if static_file.exists() and static_file.is_file():

            return send_from_directory(
                str(FLASK_STATIC_DIR),
                static_path
            )

        return jsonify({
            "error": "Static file not found",
            "path": f"/{path}"
        }), 404


    # --------------------------------------------------------
    # React/Vite static files
    # --------------------------------------------------------

    requested_file = FRONTEND_DIST / path

    if requested_file.exists() and requested_file.is_file():

        return send_from_directory(
            str(FRONTEND_DIST),
            path
        )


    # --------------------------------------------------------
    # React Router fallback
    # --------------------------------------------------------

    return serve_react_app()


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

def start_local_server():

    host = os.getenv(
        "HOST",
        config.HOST
    )

    port = int(
        os.getenv(
            "PORT",
            config.PORT
        )
    )

    print("=" * 70)
    print("MEDTRACK APPLICATION")
    print("=" * 70)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print("=" * 70)

    app.run(
        host=host,
        port=port,
        debug=False
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    start_local_server()