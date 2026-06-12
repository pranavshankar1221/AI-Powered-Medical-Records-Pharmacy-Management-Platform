"""
Alert engine — generates proactive alerts for low stock and expiry warnings.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from database.models import InventoryBatch, Medicine, Alert
import config


def check_low_stock(db: Session) -> list:
    """Find batches with quantity below threshold."""
    batches = (
        db.query(InventoryBatch)
        .filter(
            InventoryBatch.status == "active",
            InventoryBatch.quantity_remaining <= config.LOW_STOCK_THRESHOLD,
            InventoryBatch.quantity_remaining > 0,
        )
        .all()
    )
    return [b.to_dict() for b in batches]


def check_expiring_soon(db: Session, days: int = None) -> list:
    """Find batches expiring within N days."""
    if days is None:
        days = config.EXPIRY_WARNING_DAYS
    cutoff = datetime.now(timezone.utc) + timedelta(days=days)
    batches = (
        db.query(InventoryBatch)
        .filter(
            InventoryBatch.status == "active",
            InventoryBatch.expiry_date <= cutoff,
            InventoryBatch.expiry_date > datetime.now(timezone.utc),
            InventoryBatch.quantity_remaining > 0,
        )
        .order_by(InventoryBatch.expiry_date.asc())
        .all()
    )
    return [b.to_dict() for b in batches]


def check_expired(db: Session) -> list:
    """Find expired batches that still have stock."""
    now = datetime.now(timezone.utc)
    batches = (
        db.query(InventoryBatch)
        .filter(
            InventoryBatch.expiry_date <= now,
            InventoryBatch.quantity_remaining > 0,
        )
        .order_by(InventoryBatch.expiry_date.asc())
        .all()
    )
    # Mark expired batches
    for b in batches:
        if b.status != "expired":
            b.status = "expired"
    db.commit()
    return [b.to_dict() for b in batches]


def generate_alerts(db: Session) -> dict:
    """Run all alert checks and return summary."""
    low_stock = check_low_stock(db)
    expiring_30 = check_expiring_soon(db, 30)
    expiring_60 = check_expiring_soon(db, 60)
    expiring_90 = check_expiring_soon(db, 90)
    expired = check_expired(db)

    return {
        "low_stock": low_stock,
        "low_stock_count": len(low_stock),
        "expiring_30_days": expiring_30,
        "expiring_30_count": len(expiring_30),
        "expiring_60_days": expiring_60,
        "expiring_60_count": len(expiring_60),
        "expiring_90_days": expiring_90,
        "expiring_90_count": len(expiring_90),
        "expired": expired,
        "expired_count": len(expired),
    }
