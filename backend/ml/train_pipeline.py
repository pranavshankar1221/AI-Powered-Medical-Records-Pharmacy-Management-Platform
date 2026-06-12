"""
Unified ML training pipeline — trains both models and logs to MLflow.
"""

import sys
from pathlib import Path

# Add parent to path so imports work when run standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.demand_model import train_demand_model
from ml.expiry_model import train_expiry_model

import config


def run_pipeline():
    """Train all ML models with MLflow tracking."""
    print("=" * 60)
    print("MEDIQR MLOPS — Model Training Pipeline")
    print("=" * 60)

    models_dir = config.MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    # Try MLflow tracking
    try:
        import mlflow
        mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)
        mlflow.set_experiment(config.MLFLOW_EXPERIMENT_NAME)
        use_mlflow = True
        print(f"[OK] MLflow tracking at: {config.MLFLOW_TRACKING_URI}")
    except Exception as e:
        print(f"[WARNING] MLflow not available: {e}. Training without tracking.")
        use_mlflow = False

    # ── Train Demand Model ───────────────────────────────────────────────
    print("\n[1/2] Training Demand Prediction Model...")

    if use_mlflow:
        with mlflow.start_run(run_name="demand_model_training"):
            metrics = train_demand_model(models_dir)
            mlflow.log_params({
                "model_type": "RandomForestRegressor",
                "n_estimators": 100,
                "max_depth": 12,
            })
            mlflow.log_metrics({
                "demand_mse": metrics["mse"],
                "demand_rmse": metrics["rmse"],
                "demand_r2": metrics["r2_score"],
                "demand_mae": metrics["mae"],
            })
            mlflow.log_artifact(str(models_dir / "demand_model.joblib"))
    else:
        metrics = train_demand_model(models_dir)

    print(f"  ✅ Demand Model — R²: {metrics['r2_score']}, RMSE: {metrics['rmse']}")

    # ── Train Expiry Model ───────────────────────────────────────────────
    print("\n[2/2] Training Expiry Risk Model...")

    if use_mlflow:
        with mlflow.start_run(run_name="expiry_model_training"):
            metrics = train_expiry_model(models_dir)
            mlflow.log_params({
                "model_type": "RandomForestClassifier",
                "n_estimators": 100,
                "max_depth": 10,
            })
            mlflow.log_metrics({
                "expiry_accuracy": metrics["accuracy"],
            })
            mlflow.log_artifact(str(models_dir / "expiry_model.joblib"))
    else:
        metrics = train_expiry_model(models_dir)

    print(f"  ✅ Expiry Model — Accuracy: {metrics['accuracy']}")

    print("\n" + "=" * 60)
    print("✅ All models trained successfully!")
    print(f"   Models saved to: {models_dir}")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
