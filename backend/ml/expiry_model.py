"""
Expiry Risk Prediction Model — RandomForestClassifier.

Input features:
- current_stock
- sales_velocity (units/day)
- days_until_expiry

Output:
- risk_level: Low | Medium | High
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import json
from pathlib import Path


def generate_training_data(n_samples: int = 3000) -> pd.DataFrame:
    """Generate synthetic training data for expiry risk classification."""
    np.random.seed(42)

    data = []
    for _ in range(n_samples):
        stock = np.random.randint(1, 500)
        velocity = np.random.uniform(0, 20)  # units per day
        days_remaining = np.random.randint(0, 365)

        # Calculate risk label
        if days_remaining <= 0:
            risk = 2  # High
        elif velocity == 0 and days_remaining < 90:
            risk = 2  # High — no sales and expiring soon
        elif stock > 0 and velocity > 0:
            days_to_sell = stock / velocity
            if days_to_sell > days_remaining * 0.8:
                risk = 2  # High — won't sell before expiry
            elif days_to_sell > days_remaining * 0.5:
                risk = 1  # Medium
            else:
                risk = 0  # Low
        elif days_remaining < 30:
            risk = 2
        elif days_remaining < 90:
            risk = 1
        else:
            risk = 0

        data.append({
            "current_stock": stock,
            "sales_velocity": round(velocity, 2),
            "days_until_expiry": days_remaining,
            "risk_label": risk,
        })

    return pd.DataFrame(data)


def train_expiry_model(save_dir: Path) -> dict:
    """Train the expiry risk classification model."""
    df = generate_training_data()

    features = ["current_stock", "sales_velocity", "days_until_expiry"]
    X = df[features]
    y = df["risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=["Low", "Medium", "High"], output_dict=True)

    # Save model
    model_path = save_dir / "expiry_model.joblib"
    joblib.dump(model, model_path)

    # Save metrics
    metrics = {
        "model": "RandomForestClassifier",
        "features": features,
        "accuracy": round(accuracy, 4),
        "classification_report": report,
        "n_estimators": 100,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
    }

    metrics_path = save_dir.parent / "metrics" / "expiry_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics
