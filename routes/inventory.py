"""
routes/inventory.py
B2B Inventory Management Routes – CRUD for batches, medicines, and alerts.
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
import json

from database.db import get_session
from database.models import Medicine, InventoryBatch, Alert
from services.alert_engine import run_alert_checks

inventory_bp = Blueprint("inventory", __name__)


# ── Medicine Catalogue ───────────────────────────────────────────────────────

@inventory_bp.get("/api/medicines")
def list_medicines():
    """Return all medicines in the catalogue with optional search."""
    q = request.args.get("q", "").strip()
    with get_session() as session:
        query = session.query(Medicine)
        if q:
            query = query.filter(
                Medicine.name.ilike(f"%{q}%") |
                Medicine.generic_name.ilike(f"%{q}%") |
                Medicine.category.ilike(f"%{q}%")
            )
        medicines = query.order_by(Medicine.name).all()
        return jsonify([m.to_dict() for m in medicines])


@inventory_bp.get("/api/medicines/<int:med_id>")
def get_medicine(med_id):
    """Return details for a single medicine."""
    with get_session() as session:
        med = session.get(Medicine, med_id)
        if not med:
            return jsonify({"error": "Medicine not found"}), 404
        d = med.to_dict()
        # include current stock summary
        batches = (
            session.query(InventoryBatch)
            .filter(
                InventoryBatch.medicine_id == med.medicine_id,
                InventoryBatch.status == "active"
            )
            .all()
        )
        d["total_stock"] = sum(b.quantity_remaining for b in batches)
        d["active_batches"] = len(batches)
        return jsonify(d)


# ── Inventory Batches ────────────────────────────────────────────────────────

@inventory_bp.get("/api/inventory")
def list_inventory():
    """List all inventory batches with optional filters."""
    status = request.args.get("status")          # active | expired | recalled
    low_stock = request.args.get("low_stock")    # true
    expiring_days = request.args.get("expiring_days", type=int)
    medicine_id = request.args.get("medicine_id")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    with get_session() as session:
        # Run alert checks before returning data
        run_alert_checks(session)

        query = session.query(InventoryBatch).join(
            Medicine, InventoryBatch.medicine_id == Medicine.medicine_id
        )

        if status:
            query = query.filter(InventoryBatch.status == status)
        if medicine_id:
            query = query.filter(InventoryBatch.medicine_id == medicine_id)
        if low_stock == "true":
            import config as _cfg
            query = query.filter(
                InventoryBatch.quantity_remaining <= _cfg.LOW_STOCK_THRESHOLD,
                InventoryBatch.status == "active"
            )
        if expiring_days:
            cutoff = datetime.now(timezone.utc) + timedelta(days=expiring_days)
            query = query.filter(
                InventoryBatch.expiry_date <= cutoff,
                InventoryBatch.status == "active"
            )

        total = query.count()
        batches = (
            query.order_by(InventoryBatch.expiry_date)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return jsonify({
            "total": total,
            "page": page,
            "per_page": per_page,
            "batches": [b.to_dict() for b in batches]
        })


@inventory_bp.post("/api/inventory/scan")
def scan_shipment():
    """
    Simulate scanning a manufacturer QR code on an incoming shipment.
    Expected JSON body:
    {
        "medicine_id": "MED_001",
        "batch_number": "BATCH-2026-A1",
        "manufacture_date": "2026-01-15",
        "expiry_date": "2028-01-14",
        "quantity_received": 200,
        "supplier": "ABC Pharma Distributors",
        "manufacturer_qr_data": "<raw QR string from box>"
    }
    """
    data = request.get_json()
    required = ["medicine_id", "batch_number", "expiry_date", "quantity_received"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    with get_session() as session:
        # Verify medicine exists
        med = session.query(Medicine).filter_by(medicine_id=data["medicine_id"]).first()
        if not med:
            return jsonify({"error": f"Medicine ID '{data['medicine_id']}' not found in catalogue"}), 404

        # Check duplicate batch
        existing = session.query(InventoryBatch).filter_by(
            batch_number=data["batch_number"],
            medicine_id=data["medicine_id"]
        ).first()
        if existing:
            return jsonify({"error": "Batch number already exists for this medicine"}), 409

        # Parse dates
        try:
            expiry = datetime.strptime(data["expiry_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            mfg = (
                datetime.strptime(data["manufacture_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if data.get("manufacture_date") else None
            )
        except ValueError as e:
            return jsonify({"error": f"Invalid date format: {e}"}), 400

        batch = InventoryBatch(
            medicine_id=data["medicine_id"],
            batch_number=data["batch_number"],
            manufacture_date=mfg,
            expiry_date=expiry,
            quantity_received=int(data["quantity_received"]),
            quantity_remaining=int(data["quantity_received"]),
            supplier=data.get("supplier", "Unknown"),
            manufacturer_qr_data=data.get("manufacturer_qr_data"),
            status="active",
        )
        session.add(batch)
        session.flush()

        # Immediately run alert checks for this new batch
        run_alert_checks(session)
        session.commit()

        return jsonify({
            "message": "Shipment scanned and logged successfully",
            "batch": batch.to_dict()
        }), 201


@inventory_bp.get("/api/inventory/<int:batch_id>")
def get_batch(batch_id):
    """Return details for a single inventory batch."""
    with get_session() as session:
        batch = session.get(InventoryBatch, batch_id)
        if not batch:
            return jsonify({"error": "Batch not found"}), 404
        return jsonify(batch.to_dict())


@inventory_bp.put("/api/inventory/<int:batch_id>")
def update_batch(batch_id):
    """
    Update batch quantity (dispensed/adjusted) or status.
    Body: { "quantity_remaining": 150, "status": "active" }
    """
    data = request.get_json()
    with get_session() as session:
        batch = session.get(InventoryBatch, batch_id)
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        if "quantity_remaining" in data:
            qty = int(data["quantity_remaining"])
            if qty < 0:
                return jsonify({"error": "Quantity cannot be negative"}), 400
            if qty > batch.quantity_received:
                return jsonify({"error": "Quantity exceeds received amount"}), 400
            batch.quantity_remaining = qty

        if "status" in data and data["status"] in ("active", "expired", "recalled"):
            batch.status = data["status"]

        run_alert_checks(session)
        session.commit()
        return jsonify({"message": "Batch updated", "batch": batch.to_dict()})


# ── Alerts ──────────────────────────────────────────────────────────────────

@inventory_bp.get("/api/inventory/alerts")
def get_alerts():
    """Return all active (unresolved) alerts, sorted by severity."""
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    with get_session() as session:
        run_alert_checks(session)
        alerts = (
            session.query(Alert)
            .filter_by(is_resolved=False)
            .order_by(Alert.created_at.desc())
            .all()
        )
        data = sorted([a.to_dict() for a in alerts], key=lambda x: severity_order.get(x["severity"], 9))
        return jsonify({"count": len(data), "alerts": data})


@inventory_bp.post("/api/inventory/alerts/<int:alert_id>/resolve")
def resolve_alert(alert_id):
    """Mark an alert as resolved."""
    with get_session() as session:
        alert = session.get(Alert, alert_id)
        if not alert:
            return jsonify({"error": "Alert not found"}), 404
        alert.is_resolved = True
        session.commit()
        return jsonify({"message": "Alert resolved", "alert": alert.to_dict()})


@inventory_bp.get("/api/inventory/stats")
def inventory_stats():
    """Return dashboard-level statistics."""
    with get_session() as session:
        run_alert_checks(session)

        total_batches = session.query(InventoryBatch).filter_by(status="active").count()
        total_medicines = session.query(Medicine).count()
        low_stock_count = session.query(InventoryBatch).filter(
            InventoryBatch.quantity_remaining <= 10,
            InventoryBatch.status == "active"
        ).count()
        expiring_soon = session.query(InventoryBatch).filter(
            InventoryBatch.expiry_date <= datetime.now(timezone.utc) + timedelta(days=30),
            InventoryBatch.status == "active"
        ).count()
        active_alerts = session.query(Alert).filter_by(is_resolved=False).count()
        critical_alerts = session.query(Alert).filter_by(is_resolved=False, severity="critical").count()

        total_stock = session.query(
            func.sum(InventoryBatch.quantity_remaining)
        ).filter_by(status="active").scalar() or 0

        return jsonify({
            "total_medicines": total_medicines,
            "active_batches": total_batches,
            "total_stock_units": int(total_stock),
            "low_stock_batches": low_stock_count,
            "expiring_soon": expiring_soon,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
        })
