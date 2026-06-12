"""
Inventory management routes — CRUD for medicines and batches.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
import uuid

from database.base import get_db
from database.models import Medicine, InventoryBatch
from schemas.medicine import MedicineCreate, MedicineUpdate, BatchCreate, BatchUpdate
from utils.security import require_role
from utils.exceptions import NotFoundException, DuplicateException
from utils.pagination import PaginationParams, PaginatedResponse

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("/medicines")
def list_medicines(
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    category: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "pharmacist")),
):
    """List all medicines with search, filter, and pagination."""
    query = db.query(Medicine)

    if search:
        query = query.filter(
            Medicine.name.ilike(f"%{search}%")
            | Medicine.generic_name.ilike(f"%{search}%")
            | Medicine.medicine_id.ilike(f"%{search}%")
        )
    if category:
        query = query.filter(Medicine.category == category)

    total = query.count()
    params = PaginationParams(page=page, per_page=per_page)
    medicines = query.order_by(Medicine.name).offset(params.offset).limit(params.per_page).all()

    # Enrich with total stock
    result = []
    for med in medicines:
        d = med.to_dict()
        stock = (
            db.query(func.sum(InventoryBatch.quantity_remaining))
            .filter(
                InventoryBatch.medicine_id == med.medicine_id,
                InventoryBatch.status == "active",
            )
            .scalar() or 0
        )
        d["total_stock"] = stock
        result.append(d)

    return PaginatedResponse.create(result, total, params.page, params.per_page).model_dump()


@router.get("/medicines/{medicine_id}")
def get_medicine(
    medicine_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "pharmacist")),
):
    """Get a single medicine with its batches."""
    med = db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
    if not med:
        raise NotFoundException("Medicine")

    batches = (
        db.query(InventoryBatch)
        .filter(InventoryBatch.medicine_id == medicine_id)
        .order_by(InventoryBatch.expiry_date.asc())
        .all()
    )

    return {
        "success": True,
        "data": {
            **med.to_dict(),
            "batches": [b.to_dict() for b in batches],
        },
    }


@router.post("/medicines")
def create_medicine(
    req: MedicineCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Add a new medicine to the catalogue."""
    medicine_id = f"MED-{uuid.uuid4().hex[:8].upper()}"

    med = Medicine(
        medicine_id=medicine_id,
        name=req.name,
        generic_name=req.generic_name,
        category=req.category,
        manufacturer=req.manufacturer,
        dosage_form=req.dosage_form,
        strength=req.strength,
        description=req.description,
        purpose=req.purpose,
        side_effects=req.side_effects,
        interactions=req.interactions,
        contraindications=req.contraindications,
        storage_instructions=req.storage_instructions,
        dosage_schedule=req.dosage_schedule,
        food_instructions=req.food_instructions,
        missed_dose_guidance=req.missed_dose_guidance,
        unit_price=req.unit_price,
    )
    db.add(med)
    db.commit()
    db.refresh(med)

    return {"success": True, "data": med.to_dict()}


@router.put("/medicines/{medicine_id}")
def update_medicine(
    medicine_id: str,
    req: MedicineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Update an existing medicine."""
    med = db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
    if not med:
        raise NotFoundException("Medicine")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(med, key, value)

    db.commit()
    db.refresh(med)
    return {"success": True, "data": med.to_dict()}


@router.delete("/medicines/{medicine_id}")
def delete_medicine(
    medicine_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Delete a medicine and all its batches."""
    med = db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
    if not med:
        raise NotFoundException("Medicine")

    db.query(InventoryBatch).filter(InventoryBatch.medicine_id == medicine_id).delete()
    db.delete(med)
    db.commit()
    return {"success": True, "message": "Medicine deleted successfully"}


# ── Batch Endpoints ──────────────────────────────────────────────────────────

@router.get("/batches")
def list_batches(
    page: int = 1,
    per_page: int = 20,
    medicine_id: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "pharmacist")),
):
    """List inventory batches with filters."""
    query = db.query(InventoryBatch)
    if medicine_id:
        query = query.filter(InventoryBatch.medicine_id == medicine_id)
    if status:
        query = query.filter(InventoryBatch.status == status)

    total = query.count()
    params = PaginationParams(page=page, per_page=per_page)
    batches = query.order_by(InventoryBatch.expiry_date.asc()).offset(params.offset).limit(params.per_page).all()

    return PaginatedResponse.create(
        [b.to_dict() for b in batches], total, params.page, params.per_page
    ).model_dump()


@router.post("/batches")
def create_batch(
    req: BatchCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Add a new inventory batch."""
    # Verify medicine exists
    med = db.query(Medicine).filter(Medicine.medicine_id == req.medicine_id).first()
    if not med:
        raise NotFoundException("Medicine")

    # Check duplicate batch number
    existing = db.query(InventoryBatch).filter(InventoryBatch.batch_number == req.batch_number).first()
    if existing:
        raise DuplicateException("Batch number")

    batch = InventoryBatch(
        medicine_id=req.medicine_id,
        batch_number=req.batch_number,
        manufacture_date=datetime.fromisoformat(req.manufacture_date) if req.manufacture_date else None,
        expiry_date=datetime.fromisoformat(req.expiry_date),
        quantity_received=req.quantity_received,
        quantity_remaining=req.quantity_received,
        supplier=req.supplier,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    return {"success": True, "data": batch.to_dict()}


@router.get("/categories")
def list_categories(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "pharmacist")),
):
    """Get all unique medicine categories."""
    cats = (
        db.query(Medicine.category)
        .filter(Medicine.category.isnot(None), Medicine.category != "")
        .distinct()
        .all()
    )
    return {"success": True, "data": [c[0] for c in cats]}


@router.get("/alerts")
def get_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Get all inventory alerts (low stock, expiry warnings)."""
    from services.alert_engine import generate_alerts
    alerts = generate_alerts(db)
    return {"success": True, "data": alerts}
