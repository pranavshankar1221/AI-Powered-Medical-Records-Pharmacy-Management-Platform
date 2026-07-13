"""
Medicine Demand Prediction Model — RandomForestRegressor.

Input features:
- current_stock
- month (1-12)
- avg_monthly_sales
- category_encoded

Output:
- predicted_demand_30_days
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import json
from pathlib import Path


def generate_training_data(n_samples: int = 2000) -> pd.DataFrame:
    """Generate synthetic training data for demand prediction."""
    np.random.seed(42)

    categories = ["Analgesic", "Antibiotic", "Antacid", "Antihistamine",
                   "Antipyretic", "Vitamin", "Anti-inflammatory", "Antihypertensive"]

    data = []
    for _ in range(n_samples):
        category = np.random.choice(categories)
        month = np.random.randint(1, 13)
        current_stock = np.random.randint(5, 500)
        avg_monthly_sales = np.random.uniform(10, 200)

        # Seasonal factor
        seasonal_factor = 1.0
        if month in [6, 7, 8]:  # Monsoon — higher demand for antipyretics
            seasonal_factor = 1.3 if category in ["Antipyretic", "Antibiotic"] else 1.0
        elif month in [11, 12, 1]:  # Winter — cough/cold meds
            seasonal_factor = 1.2 if category in ["Antihistamine", "Analgesic"] else 1.0

        # Base demand
        demand = avg_monthly_sales * seasonal_factor + np.random.normal(0, avg_monthly_sales * 0.1)
        demand = max(0, demand)

        data.append({
            "current_stock": current_stock,
            "month": month,
            "avg_monthly_sales": avg_monthly_sales,
            "category_encoded": categories.index(category),
            "demand_30_days": round(demand, 1),
        })

    return pd.DataFrame(data)


def train_demand_model(save_dir: Path) -> dict:
    """Train the demand prediction model."""
    df = generate_training_data()

    features = ["current_stock", "month", "avg_monthly_sales", "category_encoded"]
    X = df[features]
    y = df["demand_30_days"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    # Save model
    model_path = save_dir / "demand_model.joblib"
    joblib.dump(model, model_path)

    # Save metrics
    metrics = {
        "model": "RandomForestRegressor",
        "features": features,
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "r2_score": round(r2, 4),
        "mae": round(mae, 4),
        "n_estimators": 100,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
    }

    metrics_path = save_dir.parent / "metrics" / "demand_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics
