"""
app.py
Main entry point for MedTrack. Registers Blueprints, sets up HTML page rendering, and runs the server.
"""

from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
from pathlib import Path

# Add ai_module to sys.path to resolve RAG engine imports
sys.path.insert(0, str(Path(__file__).resolve().parent / "ai_module"))

import config
from database.db import init_db
from routes.inventory import inventory_bp
from routes.billing import billing_bp
from routes.patient import patient_bp
from mlops.monitor import get_drift_metrics, get_inference_logs

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
CORS(app)

# Ensure database tables exist
init_db()

# Register Blueprints
app.register_blueprint(inventory_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(patient_bp)


# ── Page Renders ──────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/dashboard")
def dashboard_page():
    """B2B Inventory & Operations Dashboard"""
    return render_template("dashboard.html")


@app.route("/billing")
def billing_page():
    """B2B Smart Billing QR Receipt Creator"""
    return render_template("billing.html")


@app.route("/patient")
def patient_page():
    """B2C Patient Companion / Medicine Cabinet & Chatbot"""
    return render_template("patient.html")


# ── Monitoring & Drift Endpoint ──────────────────────────────────────────────

@app.route("/monitoring")
def monitoring_page():
    """Render MLOps Dashboard & System Performance Metrics"""
    return render_template("monitoring.html")


@app.route("/api/mlops/metrics")
def get_monitoring_metrics():
    """API endpoint providing drift and latency statistics."""
    metrics = get_drift_metrics()
    recent_logs = get_inference_logs(15)
    return jsonify({
        "metrics": metrics,
        "logs": recent_logs
    })


@app.route("/static/<path:path>")
def serve_static(path):
    """Fallback static asset server."""
    return send_from_directory("static", path)


# ── App Startup ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--host", type=str, default=config.HOST)
    args = parser.parse_args()

    # Make sure FAISS index is loaded on start if present
    from services.rag_engine import ensure_index_loaded
    if ensure_index_loaded():
        print("[OK] FAISS index loaded successfully into RAG Engine.")
    else:
        print("[WARNING] FAISS index files not found in data/faiss_index/. Please run knowledge_base/build_index.py.")

    print(f"MedTrack App starting on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=config.DEBUG)
