"""
ML prediction routes — demand prediction and expiry risk classification.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.base import get_db
from schemas.ml import (
    DemandPredictionRequest, DemandPredictionResponse,
    ExpiryRiskRequest, ExpiryRiskResponse,
)
from utils.security import require_role

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])


@router.post("/predict-demand", response_model=DemandPredictionResponse)
def predict_demand(
    req: DemandPredictionRequest,
    current_user=Depends(require_role("admin", "pharmacist")),
):
    """Predict medicine demand for the next 30 days."""
    from ml.serve import predict_demand as ml_predict

    result = ml_predict(
        current_stock=req.current_stock,
        month=req.month,
        avg_monthly_sales=req.avg_monthly_sales,
        category=req.category or "General",
    )

    return DemandPredictionResponse(
        medicine_id=req.medicine_id,
        predicted_demand_30_days=result["predicted_demand"],
        confidence=result["confidence"],
        recommendation=result["recommendation"],
    )


@router.post("/predict-expiry-risk", response_model=ExpiryRiskResponse)
def predict_expiry_risk(
    req: ExpiryRiskRequest,
    current_user=Depends(require_role("admin", "pharmacist")),
):
    """Predict expiry risk for a medicine batch."""
    from ml.serve import predict_expiry_risk as ml_predict

    result = ml_predict(
        current_stock=req.current_stock,
        sales_velocity=req.sales_velocity,
        days_until_expiry=req.days_until_expiry,
    )

    return ExpiryRiskResponse(
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        recommendation=result["recommendation"],
    )


@router.get("/model-info")
def get_model_info(
    current_user=Depends(require_role("admin")),
):
    """Get information about deployed ML models."""
    from ml.serve import get_model_info as ml_info
    info = ml_info()
    return {"success": True, "data": info}


@router.get("/batch-predictions")
def batch_expiry_predictions(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Run expiry risk prediction on all active batches."""
    from database.models import InventoryBatch, SalesLog
    from ml.serve import predict_expiry_risk as ml_predict
    from sqlalchemy import func
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    batches = (
        db.query(InventoryBatch)
        .filter(InventoryBatch.status == "active", InventoryBatch.quantity_remaining > 0)
        .all()
    )

    predictions = []
    for batch in batches:
        days_until_expiry = max(0, (batch.expiry_date - now).days)

        # Calculate sales velocity
        total_sold = (
            db.query(func.sum(SalesLog.quantity_sold))
            .filter(SalesLog.medicine_id == batch.medicine_id)
            .scalar() or 0
        )
        days_since_received = max(1, (now - batch.received_at).days) if batch.received_at else 30
        velocity = total_sold / days_since_received

        result = ml_predict(
            current_stock=batch.quantity_remaining,
            sales_velocity=velocity,
            days_until_expiry=days_until_expiry,
        )

        predictions.append({
            "batch_id": batch.id,
            "batch_number": batch.batch_number,
            "medicine_id": batch.medicine_id,
            "medicine_name": batch.medicine.name if batch.medicine else None,
            "quantity_remaining": batch.quantity_remaining,
            "expiry_date": batch.expiry_date.isoformat(),
            "days_until_expiry": days_until_expiry,
            **result,
        })

    # Sort by risk score descending
    predictions.sort(key=lambda x: x.get("risk_score", 0), reverse=True)

    return {"success": True, "data": predictions}
