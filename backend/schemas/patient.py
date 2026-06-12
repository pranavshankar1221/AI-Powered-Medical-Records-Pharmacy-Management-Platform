"""
Pydantic schemas for patient-facing endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time


class ReminderCreate(BaseModel):
    medicine_name: str = Field(..., max_length=200)
    dosage: Optional[str] = ""
    time_of_day: str = Field(default="morning")  # morning | afternoon | night | custom
    custom_time: Optional[str] = None  # HH:MM format
    scheduled_date: Optional[str] = None  # YYYY-MM-DD format
    notes: Optional[str] = ""


class ReminderUpdate(BaseModel):
    medicine_name: Optional[str] = None
    dosage: Optional[str] = None
    time_of_day: Optional[str] = None
    custom_time: Optional[str] = None
    scheduled_date: Optional[str] = None
    status: Optional[str] = None  # taken | pending | missed
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class QRScanRequest(BaseModel):
    bill_token: str = Field(..., min_length=1)

class AutoSetReminderRequest(BaseModel):
    bill_token: str = Field(..., min_length=1)


class PatientMedicineResponse(BaseModel):
    medicine_name: str
    manufacturer: Optional[str]
    batch_number: Optional[str]
    expiry_date: Optional[str]
    purpose: Optional[str]
    dosage_instructions: Optional[str]
    food_instructions: Optional[str]
    side_effects: Optional[str]
    quantity: int
    unit_price: float
    ai_explanation: Optional[str] = None
    disclaimer: str = "This information is for awareness only. Follow your doctor's prescription."
