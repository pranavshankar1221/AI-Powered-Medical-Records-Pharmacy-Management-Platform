"""
Patient-facing routes — dashboard, reminders, QR scan, AI explanations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date, time, timezone

from database.base import get_db
from database.models import Reminder, Invoice, InvoiceItem, User
from schemas.patient import ReminderCreate, ReminderUpdate, QRScanRequest, AutoSetReminderRequest
from services.ai_explainer import generate_ai_explanation, generate_prescription_summary
from utils.security import get_current_user, require_role
from utils.exceptions import NotFoundException

router = APIRouter(prefix="/api/patient", tags=["Patient"])


@router.get("/dashboard")
async def patient_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get patient dashboard overview."""
    today = date.today()

    # Get today's reminders
    reminders = (
        db.query(Reminder)
        .filter(
            Reminder.user_id == current_user.id,
            Reminder.is_active == True,
        )
        .order_by(Reminder.created_at.desc())
        .all()
    )

    today_reminders = [r for r in reminders if r.scheduled_date == today or r.scheduled_date is None]
    taken_count = len([r for r in today_reminders if r.status == "taken"])
    pending_count = len([r for r in today_reminders if r.status == "pending"])
    missed_count = len([r for r in today_reminders if r.status == "missed"])

    # Get recent bills (by patient name match)
    recent_bills = (
        db.query(Invoice)
        .filter(Invoice.patient_name.ilike(f"%{current_user.full_name}%"))
        .order_by(Invoice.created_at.desc())
        .limit(10)
        .all()
    )

    # Collect unique active medicines from recent bills
    active_medicines = set()
    for bill in recent_bills[:5]:
        for item in bill.items:
            if item.medicine:
                active_medicines.add(item.medicine.name)

    return {
        "success": True,
        "data": {
            "user": current_user.to_dict(),
            "reminders_today": {
                "total": len(today_reminders),
                "taken": taken_count,
                "pending": pending_count,
                "missed": missed_count,
            },
            "active_medicines": list(active_medicines),
            "active_medicines_count": len(active_medicines),
            "recent_bills": [
                {
                    "invoice_number": b.invoice_number,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                    "final_amount": b.final_amount,
                    "item_count": len(b.items),
                }
                for b in recent_bills[:5]
            ],
            "total_reminders": len(reminders),
        },
    }


# ── Reminders ────────────────────────────────────────────────────────────────

@router.get("/reminders")
def list_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all reminders for the current patient."""
    reminders = (
        db.query(Reminder)
        .filter(Reminder.user_id == current_user.id)
        .order_by(Reminder.created_at.desc())
        .all()
    )
    return {"success": True, "data": [r.to_dict() for r in reminders]}


@router.post("/reminders")
def create_reminder(
    req: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new medicine reminder."""
    reminder = Reminder(
        user_id=current_user.id,
        medicine_name=req.medicine_name,
        dosage=req.dosage or "",
        time_of_day=req.time_of_day,
        custom_time=time.fromisoformat(req.custom_time) if req.custom_time else None,
        scheduled_date=date.fromisoformat(req.scheduled_date) if req.scheduled_date else None,
        notes=req.notes or "",
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return {"success": True, "data": reminder.to_dict()}


@router.put("/reminders/{reminder_id}")
def update_reminder(
    reminder_id: int,
    req: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing reminder."""
    reminder = (
        db.query(Reminder)
        .filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
        .first()
    )
    if not reminder:
        raise NotFoundException("Reminder")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "custom_time" and value:
            value = time.fromisoformat(value)
        elif key == "scheduled_date" and value:
            value = date.fromisoformat(value)
        setattr(reminder, key, value)

    db.commit()
    db.refresh(reminder)
    return {"success": True, "data": reminder.to_dict()}


@router.delete("/reminders/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a reminder."""
    reminder = (
        db.query(Reminder)
        .filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
        .first()
    )
    if not reminder:
        raise NotFoundException("Reminder")

    db.delete(reminder)
    db.commit()
    return {"success": True, "message": "Reminder deleted"}


# ── AI Explanation ───────────────────────────────────────────────────────────

@router.post("/reminders/auto-set")
def auto_set_reminders(
    req: AutoSetReminderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Auto-set reminders from a bill token."""
    invoice = db.query(Invoice).filter(Invoice.bill_token == req.bill_token).first()
    if not invoice:
        raise NotFoundException("Prescription/Bill")

    # Associate the invoice with the patient so it appears in their cabinet and scan history
    invoice.patient_name = current_user.full_name

    created_reminders = []
    
    # Map standard dosage slots to times
    slot_times = [
        time(8, 0),   # Morning
        time(13, 0),  # Afternoon
        time(20, 0),  # Night
    ]

    for item in invoice.items:
        medicine_name = item.medicine.name if item.medicine else "Unknown Medicine"
        dosage_str = item.dosage_instructions.lower().strip() if item.dosage_instructions else ""
        
        times_to_schedule = []
        
        if "-" in dosage_str:
            parts = [p.strip() for p in dosage_str.split("-")]
            for i, part in enumerate(parts):
                if i < 3 and part == "1":
                    times_to_schedule.append(slot_times[i])
        else:
            if "morning" in dosage_str:
                times_to_schedule.append(slot_times[0])
            if "afternoon" in dosage_str:
                times_to_schedule.append(slot_times[1])
            if "night" in dosage_str or "evening" in dosage_str:
                times_to_schedule.append(slot_times[2])
                
        if not times_to_schedule:
            times_to_schedule.append(time(9, 0)) # Default 9 AM if parsing fails
            
        for t in times_to_schedule:
            if t.hour < 12:
                time_of_day = "morning"
            elif t.hour < 16:
                time_of_day = "afternoon"
            elif t.hour < 19:
                time_of_day = "evening"
            else:
                time_of_day = "night"
                
            reminder = Reminder(
                user_id=current_user.id,
                medicine_name=medicine_name,
                dosage=item.dosage_instructions or "",
                time_of_day=time_of_day,
                custom_time=t,
                scheduled_date=None,  # Daily recurring
                notes=f"Auto-set from Bill ID: {req.bill_token}",
            )
            db.add(reminder)
            created_reminders.append(reminder)
            
    db.commit()
    for r in created_reminders:
        db.refresh(r)
        
    return {
        "success": True, 
        "message": f"Successfully created {len(created_reminders)} reminders.",
        "data": [r.to_dict() for r in created_reminders]
    }


@router.get("/medicine-explanation/{medicine_id}")
async def get_medicine_explanation(
    medicine_id: str,
    db: Session = Depends(get_db),
):
    """Get AI-powered patient-friendly medicine explanation. Public endpoint."""
    from database.models import Medicine
    medicine = db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
    if not medicine:
        raise NotFoundException("Medicine")

    explanation = await generate_ai_explanation(
        medicine_name=medicine.name,
        purpose=medicine.purpose or "",
        category=medicine.category or "",
        side_effects=medicine.side_effects or "",
        dosage_schedule=medicine.dosage_schedule or "",
        food_instructions=medicine.food_instructions or "",
    )

    return {
        "success": True,
        "data": {
            "medicine_name": medicine.name,
            "explanation": explanation,
            "disclaimer": "This information is for awareness only. Follow your doctor's prescription.",
        },
    }


@router.post("/prescription-summary")
async def get_prescription_summary(
    req: QRScanRequest,
    db: Session = Depends(get_db),
):
    """Generate AI prescription summary from a bill token. Public endpoint."""
    invoice = db.query(Invoice).filter(Invoice.bill_token == req.bill_token).first()
    if not invoice:
        raise NotFoundException("Bill")

    medicines = [item.to_dict() for item in invoice.items]
    summary = generate_prescription_summary(medicines)

    return {
        "success": True,
        "data": {
            "summary": summary,
            "medicines": medicines,
            "disclaimer": "This information is for awareness only. Follow your doctor's prescription.",
        },
    }
