"""
Pydantic schemas for billing endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class BillItem(BaseModel):
    medicine_id: str
    batch_id: int
    quantity: int = Field(..., ge=1)
    dosage_instructions: Optional[str] = ""


class CreateBillRequest(BaseModel):
    patient_name: str = Field(..., min_length=1, max_length=200)
    patient_phone: Optional[str] = ""
    items: List[BillItem] = Field(..., min_length=1)
    discount: float = Field(default=0.0, ge=0)


class BillResponse(BaseModel):
    id: int
    invoice_number: str
    bill_token: str
    patient_name: str
    created_at: str
    total_amount: float
    discount: float
    tax: float
    final_amount: float
    items: list
    qr_image_url: Optional[str] = None

    class Config:
        from_attributes = True
