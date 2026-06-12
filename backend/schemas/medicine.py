"""
Pydantic schemas for medicine and inventory endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MedicineCreate(BaseModel):
    name: str = Field(..., max_length=200)
    generic_name: Optional[str] = ""
    category: Optional[str] = ""
    manufacturer: Optional[str] = ""
    dosage_form: Optional[str] = ""
    strength: Optional[str] = ""
    description: Optional[str] = ""
    purpose: Optional[str] = ""
    side_effects: Optional[str] = ""
    interactions: Optional[str] = ""
    contraindications: Optional[str] = ""
    storage_instructions: Optional[str] = ""
    dosage_schedule: Optional[str] = ""
    food_instructions: Optional[str] = ""
    missed_dose_guidance: Optional[str] = ""
    unit_price: float = Field(default=0.0, ge=0)


class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    generic_name: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    side_effects: Optional[str] = None
    interactions: Optional[str] = None
    contraindications: Optional[str] = None
    storage_instructions: Optional[str] = None
    dosage_schedule: Optional[str] = None
    food_instructions: Optional[str] = None
    missed_dose_guidance: Optional[str] = None
    unit_price: Optional[float] = None


class BatchCreate(BaseModel):
    medicine_id: str = Field(..., max_length=20)
    batch_number: str = Field(..., max_length=50)
    manufacture_date: Optional[str] = None
    expiry_date: str
    quantity_received: int = Field(..., ge=1)
    supplier: Optional[str] = ""


class BatchUpdate(BaseModel):
    quantity_remaining: Optional[int] = None
    status: Optional[str] = None
    supplier: Optional[str] = None


class MedicineResponse(BaseModel):
    id: int
    medicine_id: str
    name: str
    generic_name: Optional[str]
    category: Optional[str]
    manufacturer: Optional[str]
    dosage_form: Optional[str]
    strength: Optional[str]
    description: Optional[str]
    purpose: Optional[str]
    side_effects: Optional[str]
    unit_price: float
    total_stock: Optional[int] = 0

    class Config:
        from_attributes = True
