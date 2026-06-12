"""
Pydantic schemas for ML prediction endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class DemandPredictionRequest(BaseModel):
    medicine_id: Optional[str] = None
    category: Optional[str] = None
    current_stock: int = Field(..., ge=0)
    month: int = Field(..., ge=1, le=12)
    avg_monthly_sales: float = Field(default=0.0, ge=0)


class DemandPredictionResponse(BaseModel):
    medicine_id: Optional[str]
    predicted_demand_30_days: float
    confidence: float
    recommendation: str


class ExpiryRiskRequest(BaseModel):
    current_stock: int = Field(..., ge=0)
    sales_velocity: float = Field(default=0.0, ge=0)  # units/day
    days_until_expiry: int = Field(..., ge=0)


class ExpiryRiskResponse(BaseModel):
    risk_level: str  # Low | Medium | High
    risk_score: float
    recommendation: str


class ModelMetricsResponse(BaseModel):
    model_name: str
    accuracy: Optional[float] = None
    mse: Optional[float] = None
    r2_score: Optional[float] = None
    trained_at: Optional[str] = None
    features: List[str] = []
