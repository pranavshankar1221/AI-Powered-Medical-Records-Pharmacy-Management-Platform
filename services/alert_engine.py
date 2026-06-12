"""
Proactive Alert Engine
Scans inventory for low stock, near-expiry, and expired batches.
"""

from datetime import datetime, timedelta, timezone

from database.db import get_session, shutdown_session
from database.models import InventoryBatch, Alert, Medicine
import config


def run_alert_scan():
    """
    Perform a full inventory scan and generate alerts.
    Returns a summary dict of new alerts created.
    """
    session = get_session()
    summary = {"low_stock": 0, "expiry_warning": 0, "expired": 0, "total_new": 0}

    try:
        now = datetime.utcnow()
        warning_cutoff = now + timedelta(days=config.EXPIRY_WARNING_DAYS)

        active_batches = session.query(InventoryBatch).filter(
            InventoryBatch.status.in_(["active"])
        ).all()

        for batch in active_batches:
            # ── 1. Expired batches ───────────────────────────────
            if batch.expiry_date and batch.expiry_date <= now:
                batch.status = "expired"
                if not _alert_exists(session, "expired", batch.id):
                    alert = Alert(
                        alert_type="expired",
                        batch_id=batch.id,
                        medicine_id=batch.medicine_id,
                        message=(
                            f"EXPIRED: {batch.medicine.name if batch.medicine else batch.medicine_id} "
                            f"(Batch {batch.batch_number}) expired on "
                            f"{batch.expiry_date.strftime('%Y-%m-%d')}. "
                            f"Remove from shelves immediately."
                        ),
                        severity="critical",
                    )
                    session.add(alert)
                    summary["expired"] += 1

            # ── 2. Expiry warning (within threshold days) ────────
            elif batch.expiry_date and batch.expiry_date <= warning_cutoff:
                days_remaining = (batch.expiry_date - now).days
                if not _alert_exists(session, "expiry_warning", batch.id):
                    alert = Alert(
                        alert_type="expiry_warning",
                        batch_id=batch.id,
                        medicine_id=batch.medicine_id,
                        message=(
                            f"EXPIRY WARNING: {batch.medicine.name if batch.medicine else batch.medicine_id} "
                            f"(Batch {batch.batch_number}) expires in {days_remaining} days "
                            f"on {batch.expiry_date.strftime('%Y-%m-%d')}."
                        ),
                        severity="warning",
                    )
                    session.add(alert)
                    summary["expiry_warning"] += 1

            # ── 3. Low stock ─────────────────────────────────────
            if batch.quantity_remaining <= config.LOW_STOCK_THRESHOLD and batch.status == "active":
                if not _alert_exists(session, "low_stock", batch.id):
                    alert = Alert(
                        alert_type="low_stock",
                        batch_id=batch.id,
                        medicine_id=batch.medicine_id,
                        message=(
                            f"LOW STOCK: {batch.medicine.name if batch.medicine else batch.medicine_id} "
                            f"(Batch {batch.batch_number}) has only {batch.quantity_remaining} units remaining."
                        ),
                        severity="warning" if batch.quantity_remaining > 3 else "critical",
                    )
                    session.add(alert)
                    summary["low_stock"] += 1

        session.commit()
        summary["total_new"] = summary["low_stock"] + summary["expiry_warning"] + summary["expired"]
        return summary

    except Exception as e:
        session.rollback()
        raise e
    finally:
        shutdown_session()


def get_active_alerts(limit=50):
    """Return all unresolved alerts, newest first."""
    session = get_session()
    try:
        alerts = (
            session.query(Alert)
            .filter(Alert.is_resolved == False)
            .order_by(Alert.created_at.desc())
            .limit(limit)
            .all()
        )
        return [a.to_dict() for a in alerts]
    finally:
        shutdown_session()


def get_all_alerts(include_resolved=False, limit=100):
    """Return alerts with optional resolved ones."""
    session = get_session()
    try:
        q = session.query(Alert).order_by(Alert.created_at.desc())
        if not include_resolved:
            q = q.filter(Alert.is_resolved == False)
        alerts = q.limit(limit).all()
        return [a.to_dict() for a in alerts]
    finally:
        shutdown_session()


def resolve_alert(alert_id):
    """Mark an alert as resolved."""
    session = get_session()
    try:
        alert = session.query(Alert).get(alert_id)
        if not alert:
            return None
        alert.is_resolved = True
        session.commit()
        return alert.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        shutdown_session()


def get_alert_summary():
    """Return counts by type and severity."""
    session = get_session()
    try:
        active_alerts = (
            session.query(Alert)
            .filter(Alert.is_resolved == False)
            .all()
        )
        summary = {
            "total_active": len(active_alerts),
            "critical": sum(1 for a in active_alerts if a.severity == "critical"),
            "warning": sum(1 for a in active_alerts if a.severity == "warning"),
            "info": sum(1 for a in active_alerts if a.severity == "info"),
            "by_type": {},
        }
        for a in active_alerts:
            summary["by_type"][a.alert_type] = summary["by_type"].get(a.alert_type, 0) + 1
        return summary
    finally:
        shutdown_session()


def _alert_exists(session, alert_type, batch_id):
    """Check if an unresolved alert of this type already exists for the batch."""
    return (
        session.query(Alert)
        .filter(
            Alert.alert_type == alert_type,
            Alert.batch_id == batch_id,
            Alert.is_resolved == False,
        )
        .first()
        is not None
    )


def run_alert_checks(session=None):
    """Compatibility wrapper for routes expecting a session argument.
    Delegates to run_alert_scan which handles its own session.
    The optional session parameter is ignored.
    """
    return run_alert_scan()
