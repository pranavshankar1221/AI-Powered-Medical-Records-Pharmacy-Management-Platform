"""
Billing routes — create bills, generate QR, fetch by token.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from database.base import get_db
from database.models import Medicine, InventoryBatch, Invoice, InvoiceItem, SalesLog
from schemas.billing import CreateBillRequest
from services.qr_service import generate_bill_token, generate_qr_code
from utils.security import require_role, get_current_user
from utils.exceptions import NotFoundException, InsufficientStockException
from utils.pagination import PaginationParams, PaginatedResponse
import config

router = APIRouter(prefix="/api/billing", tags=["Billing"])


@router.post("/create")
def create_bill(
    req: CreateBillRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "pharmacist")),
):
    """Create a new bill, reduce stock, generate QR code."""
    # Generate unique identifiers
    invoice_number = f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    bill_token = generate_bill_token()

    total_amount = 0.0
    invoice_items = []

    for item in req.items:
        # Validate medicine exists
        medicine = db.query(Medicine).filter(Medicine.medicine_id == item.medicine_id).first()
        if not medicine:
            raise NotFoundException(f"Medicine {item.medicine_id}")

        # Validate batch exists and has stock (with FEFO auto-resolution fallback)
        if item.batch_id:
            batch = db.query(InventoryBatch).filter(InventoryBatch.id == item.batch_id).first()
            if not batch:
                raise NotFoundException(f"Batch {item.batch_id}")
            if batch.quantity_remaining < item.quantity:
                raise InsufficientStockException(
                    medicine.name, batch.quantity_remaining, item.quantity
                )
        else:
            # Auto-resolve oldest active batch with sufficient stock (FEFO)
            batch = (
                db.query(InventoryBatch)
                .filter(
                    InventoryBatch.medicine_id == item.medicine_id,
                    InventoryBatch.status == "active",
                    InventoryBatch.expiry_date > datetime.now(timezone.utc),
                    InventoryBatch.quantity_remaining >= item.quantity
                )
                .order_by(InventoryBatch.expiry_date.asc())
                .first()
            )
            if not batch:
                # Calculate total stock to report in InsufficientStockException
                total_stock = 0
                batches = db.query(InventoryBatch).filter(
                    InventoryBatch.medicine_id == item.medicine_id,
                    InventoryBatch.status == "active"
                ).all()
                for b in batches:
                    total_stock += b.quantity_remaining
                raise InsufficientStockException(
                    medicine.name, total_stock, item.quantity
                )

        # Calculate subtotal
        subtotal = medicine.unit_price * item.quantity
        total_amount += subtotal

        # Reduce stock
        batch.quantity_remaining -= item.quantity

        # Create invoice item
        inv_item = InvoiceItem(
            batch_id=batch.id,
            medicine_id=item.medicine_id,
            quantity=item.quantity,
            unit_price=medicine.unit_price,
            subtotal=subtotal,
            dosage_instructions=item.dosage_instructions or medicine.dosage_schedule or "",
        )
        invoice_items.append(inv_item)

        # Log sale for ML pipeline
        now = datetime.now(timezone.utc)
        sale_log = SalesLog(
            medicine_id=item.medicine_id,
            quantity_sold=item.quantity,
            sale_date=now,
            month=now.month,
            year=now.year,
            revenue=subtotal,
        )
        db.add(sale_log)

    # Calculate financials
    discount = req.discount
    tax = round(total_amount * 0.05, 2)  # 5% GST
    final_amount = round(total_amount - discount + tax, 2)

    # Generate QR code (contains ONLY bill_token)
    qr_path = generate_qr_code(bill_token)

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        bill_token=bill_token,
        pharmacist_id=current_user.id,
        patient_name=req.patient_name,
        patient_phone=req.patient_phone or "",
        total_amount=round(total_amount, 2),
        discount=discount,
        tax=tax,
        final_amount=final_amount,
        qr_image_path=qr_path,
    )
    db.add(invoice)
    db.flush()  # Get invoice.id

    # Attach items
    for inv_item in invoice_items:
        inv_item.invoice_id = invoice.id
        db.add(inv_item)

    db.commit()
    db.refresh(invoice)

    return {
        "success": True,
        "data": {
            **invoice.to_dict(),
            "qr_image_url": f"/api/billing/qr/{bill_token}",
        },
    }


@router.get("/bills")
def list_bills(
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "pharmacist")),
):
    """List all bills with pagination."""
    query = db.query(Invoice)
    if search:
        query = query.filter(
            Invoice.patient_name.ilike(f"%{search}%")
            | Invoice.invoice_number.ilike(f"%{search}%")
        )

    total = query.count()
    params = PaginationParams(page=page, per_page=per_page)
    bills = query.order_by(Invoice.created_at.desc()).offset(params.offset).limit(params.per_page).all()

    return PaginatedResponse.create(
        [b.to_dict() for b in bills], total, params.page, params.per_page
    ).model_dump()


@router.get("/bills/{bill_id}")
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "pharmacist")),
):
    """Get a specific bill by ID."""
    invoice = db.query(Invoice).filter(Invoice.id == bill_id).first()
    if not invoice:
        raise NotFoundException("Invoice")
    return {"success": True, "data": invoice.to_dict()}


@router.get("/qr/{bill_token}")
def get_qr_image(bill_token: str):
    """Serve QR code image for a bill token."""
    filepath = config.QR_DIR / f"{bill_token}.png"
    if not filepath.exists():
        raise NotFoundException("QR Code")
    return FileResponse(str(filepath), media_type="image/png")


@router.get("/scan/{bill_token}")
def scan_bill(bill_token: str, db: Session = Depends(get_db)):
    """
    Public endpoint — patient scans QR to get bill details.
    No authentication required.
    """
    invoice = db.query(Invoice).filter(Invoice.bill_token == bill_token).first()
    if not invoice:
        raise NotFoundException("Bill")

    return {
        "success": True,
        "data": {
            "invoice_number": invoice.invoice_number,
            "patient_name": invoice.patient_name,
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
            "total_amount": invoice.total_amount,
            "discount": invoice.discount,
            "tax": invoice.tax,
            "final_amount": invoice.final_amount,
            "items": [item.to_dict() for item in invoice.items],
            "pharmacy_name": config.PHARMACY_NAME,
            "disclaimer": "This information is for awareness only. Follow your doctor's prescription.",
        },
    }
