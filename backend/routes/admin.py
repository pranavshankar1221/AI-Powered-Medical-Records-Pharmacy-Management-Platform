"""
Admin dashboard and analytics routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta, timezone

from database.base import get_db
from database.models import (
    Medicine, InventoryBatch, Invoice, InvoiceItem, User, SalesLog, Alert
)
from utils.security import require_role
from services.alert_engine import generate_alerts

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])


@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Get all KPI metrics for the admin dashboard."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Revenue metrics
    total_revenue = db.query(func.sum(Invoice.final_amount)).scalar() or 0
    today_revenue = (
        db.query(func.sum(Invoice.final_amount))
        .filter(Invoice.created_at >= today_start)
        .scalar() or 0
    )
    monthly_revenue = (
        db.query(func.sum(Invoice.final_amount))
        .filter(Invoice.created_at >= month_start)
        .scalar() or 0
    )

    # Counts
    total_medicines = db.query(Medicine).count()
    total_bills = db.query(Invoice).count()
    total_patients = db.query(User).filter(User.role == "patient").count()
    total_pharmacists = db.query(User).filter(User.role == "pharmacist").count()

    # Alerts
    alerts = generate_alerts(db)

    # Fast/slow moving medicines (based on sales volume)
    fast_moving = (
        db.query(
            SalesLog.medicine_id,
            Medicine.name,
            func.sum(SalesLog.quantity_sold).label("total_sold"),
        )
        .join(Medicine, Medicine.medicine_id == SalesLog.medicine_id)
        .group_by(SalesLog.medicine_id, Medicine.name)
        .order_by(func.sum(SalesLog.quantity_sold).desc())
        .limit(5)
        .all()
    )

    slow_moving = (
        db.query(
            SalesLog.medicine_id,
            Medicine.name,
            func.sum(SalesLog.quantity_sold).label("total_sold"),
        )
        .join(Medicine, Medicine.medicine_id == SalesLog.medicine_id)
        .group_by(SalesLog.medicine_id, Medicine.name)
        .order_by(func.sum(SalesLog.quantity_sold).asc())
        .limit(5)
        .all()
    )

    return {
        "success": True,
        "data": {
            "total_revenue": round(total_revenue, 2),
            "today_revenue": round(today_revenue, 2),
            "monthly_revenue": round(monthly_revenue, 2),
            "total_medicines": total_medicines,
            "total_bills": total_bills,
            "total_patients": total_patients,
            "total_pharmacists": total_pharmacists,
            "low_stock_count": alerts["low_stock_count"],
            "expiring_soon_count": alerts["expiring_30_count"],
            "expired_count": alerts["expired_count"],
            "fast_moving": [
                {"medicine_id": fm[0], "name": fm[1], "total_sold": fm[2]}
                for fm in fast_moving
            ],
            "slow_moving": [
                {"medicine_id": sm[0], "name": sm[1], "total_sold": sm[2]}
                for sm in slow_moving
            ],
        },
    }


@router.get("/analytics/sales-trend")
def get_sales_trend(
    months: int = 12,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Get monthly sales trend data."""
    results = (
        db.query(
            SalesLog.year,
            SalesLog.month,
            func.sum(SalesLog.quantity_sold).label("total_sold"),
            func.sum(SalesLog.revenue).label("total_revenue"),
            func.count(SalesLog.id).label("transaction_count"),
        )
        .group_by(SalesLog.year, SalesLog.month)
        .order_by(SalesLog.year.desc(), SalesLog.month.desc())
        .limit(months)
        .all()
    )

    trend = [
        {
            "year": r[0],
            "month": r[1],
            "total_sold": r[2],
            "revenue": round(r[3], 2),
            "transactions": r[4],
        }
        for r in reversed(results)
    ]
    return {"success": True, "data": trend}


@router.get("/analytics/category-analysis")
def get_category_analysis(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Get medicine category distribution and sales."""
    categories = (
        db.query(
            Medicine.category,
            func.count(Medicine.id).label("count"),
        )
        .filter(Medicine.category.isnot(None))
        .group_by(Medicine.category)
        .order_by(func.count(Medicine.id).desc())
        .all()
    )

    return {
        "success": True,
        "data": [
            {"category": c[0] or "Uncategorized", "count": c[1]}
            for c in categories
        ],
    }


@router.get("/analytics/top-medicines")
def get_top_medicines(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Get top and least selling medicines."""
    top = (
        db.query(
            SalesLog.medicine_id,
            Medicine.name,
            Medicine.category,
            func.sum(SalesLog.quantity_sold).label("total_sold"),
            func.sum(SalesLog.revenue).label("total_revenue"),
        )
        .join(Medicine, Medicine.medicine_id == SalesLog.medicine_id)
        .group_by(SalesLog.medicine_id, Medicine.name, Medicine.category)
        .order_by(func.sum(SalesLog.quantity_sold).desc())
        .limit(limit)
        .all()
    )

    least = (
        db.query(
            SalesLog.medicine_id,
            Medicine.name,
            Medicine.category,
            func.sum(SalesLog.quantity_sold).label("total_sold"),
            func.sum(SalesLog.revenue).label("total_revenue"),
        )
        .join(Medicine, Medicine.medicine_id == SalesLog.medicine_id)
        .group_by(SalesLog.medicine_id, Medicine.name, Medicine.category)
        .order_by(func.sum(SalesLog.quantity_sold).asc())
        .limit(limit)
        .all()
    )

    def format_med(m):
        return {
            "medicine_id": m[0], "name": m[1], "category": m[2],
            "total_sold": m[3], "revenue": round(m[4], 2),
        }

    return {
        "success": True,
        "data": {
            "top_selling": [format_med(m) for m in top],
            "least_selling": [format_med(m) for m in least],
        },
    }


@router.get("/analytics/inventory-distribution")
def get_inventory_distribution(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Get inventory stock distribution by category."""
    dist = (
        db.query(
            Medicine.category,
            func.sum(InventoryBatch.quantity_remaining).label("total_stock"),
        )
        .join(InventoryBatch, InventoryBatch.medicine_id == Medicine.medicine_id)
        .filter(InventoryBatch.status == "active")
        .group_by(Medicine.category)
        .all()
    )

    return {
        "success": True,
        "data": [
            {"category": d[0] or "Uncategorized", "total_stock": d[1] or 0}
            for d in dist
        ],
    }


@router.get("/users")
def get_users(
    role: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Get all users, optionally filtered by role."""
    from services.auth_service import get_all_users
    users = get_all_users(db, role=role)
    return {"success": True, "data": users}
