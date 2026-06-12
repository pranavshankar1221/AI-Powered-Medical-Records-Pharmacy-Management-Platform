"""
ML Model Serving — loads trained models and exposes prediction functions.
"""

import numpy as np
import joblib
from pathlib import Path
from typing import Optional

import config

# Cached models
_demand_model = None
_expiry_model = None

CATEGORY_MAP = {
    "Analgesic": 0, "Antibiotic": 1, "Antacid": 2, "Antihistamine": 3,
    "Antipyretic": 4, "Vitamin": 5, "Anti-inflammatory": 6, "Antihypertensive": 7,
    "General": 0,
}


def _load_model(name: str):
    """Load a joblib model from the models directory."""
    model_path = config.MODELS_DIR / f"{name}.joblib"
    if model_path.exists():
        return joblib.load(model_path)
    return None


def _get_demand_model():
    global _demand_model
    if _demand_model is None:
        _demand_model = _load_model("demand_model")
    return _demand_model


def _get_expiry_model():
    global _expiry_model
    if _expiry_model is None:
        _expiry_model = _load_model("expiry_model")
    return _expiry_model


def predict_demand(current_stock: int, month: int, avg_monthly_sales: float,
                   category: str = "General") -> dict:
    """Predict medicine demand for next 30 days."""
    model = _get_demand_model()

    if model is None:
        # Fallback: simple heuristic if model not trained yet
        predicted = avg_monthly_sales * 1.1
        return {
            "predicted_demand": round(predicted, 1),
            "confidence": 0.5,
            "recommendation": "Model not trained yet. Using simple heuristic estimate.",
        }

    category_encoded = CATEGORY_MAP.get(category, 0)
    features = np.array([[current_stock, month, avg_monthly_sales, category_encoded]])
    predicted = model.predict(features)[0]

    # Confidence based on estimator agreement
    predictions = np.array([tree.predict(features)[0] for tree in model.estimators_])
    std = np.std(predictions)
    mean = np.mean(predictions)
    confidence = max(0.1, min(0.99, 1.0 - (std / max(mean, 1))))

    # Generate recommendation
    if predicted > current_stock:
        recommendation = f"⚠️ Stock may be insufficient. Consider ordering {int(predicted - current_stock)} more units."
    elif predicted < current_stock * 0.3:
        recommendation = "✅ Stock is well above predicted demand. No action needed."
    else:
        recommendation = "📊 Stock levels are adequate for predicted demand."

    return {
        "predicted_demand": round(float(predicted), 1),
        "confidence": round(float(confidence), 3),
        "recommendation": recommendation,
    }


def predict_expiry_risk(current_stock: int, sales_velocity: float,
                         days_until_expiry: int) -> dict:
    """Predict expiry risk level for a batch."""
    model = _get_expiry_model()

    if model is None:
        # Fallback heuristic
        if days_until_expiry <= 30:
            risk_level, risk_score = "High", 0.9
        elif days_until_expiry <= 90:
            risk_level, risk_score = "Medium", 0.5
        else:
            risk_level, risk_score = "Low", 0.1

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "recommendation": "Model not trained yet. Using heuristic estimate.",
        }

    features = np.array([[current_stock, sales_velocity, days_until_expiry]])
    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]

    risk_labels = ["Low", "Medium", "High"]
    risk_level = risk_labels[prediction]
    risk_score = float(probabilities[prediction])

    # Generate recommendation
    recommendations = {
        "Low": "✅ Low expiry risk. Stock is moving well relative to expiry date.",
        "Medium": "⚠️ Medium expiry risk. Consider promotional pricing or redistribution.",
        "High": "🔴 High expiry risk! Immediate action needed — consider discounts, returns, or donation.",
    }

    return {
        "risk_level": risk_level,
        "risk_score": round(risk_score, 3),
        "recommendation": recommendations[risk_level],
    }


def get_model_info() -> dict:
    """Get information about deployed models."""
    demand_path = config.MODELS_DIR / "demand_model.joblib"
    expiry_path = config.MODELS_DIR / "expiry_model.joblib"

    import os
    from datetime import datetime

    info = {
        "demand_model": {
            "status": "loaded" if demand_path.exists() else "not_trained",
            "path": str(demand_path),
            "size_kb": round(os.path.getsize(demand_path) / 1024, 1) if demand_path.exists() else 0,
            "last_modified": datetime.fromtimestamp(os.path.getmtime(demand_path)).isoformat() if demand_path.exists() else None,
        },
        "expiry_model": {
            "status": "loaded" if expiry_path.exists() else "not_trained",
            "path": str(expiry_path),
            "size_kb": round(os.path.getsize(expiry_path) / 1024, 1) if expiry_path.exists() else 0,
            "last_modified": datetime.fromtimestamp(os.path.getmtime(expiry_path)).isoformat() if expiry_path.exists() else None,
        },
    }

    # Load metrics if available
    for model_name in ["demand", "expiry"]:
        metrics_path = config.METRICS_DIR / f"{model_name}_metrics.json"
        if metrics_path.exists():
            import json
            with open(metrics_path) as f:
                info[f"{model_name}_model"]["metrics"] = json.load(f)

    return info
