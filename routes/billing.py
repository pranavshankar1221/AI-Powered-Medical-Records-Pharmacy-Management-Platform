"""
routes/billing.py
Smart Billing Routes – invoice creation, QR code generation & retrieval.
"""

from flask import Blueprint, request, jsonify, send_file, abort
from datetime import datetime, timezone
import os
import json

from database.db import get_session
from database.models import Medicine, InventoryBatch, Invoice, InvoiceItem
from services.qr_service import generate_invoice_qr, decode_qr_payload
import config

billing_bp = Blueprint("billing", __name__)


# ── Create Invoice ────────────────────────────────────────────────────────────

@billing_bp.post("/api/billing/create")
def create_invoice():
    """
    Create a new invoice and generate a QR code.
    Body:
    {
        "patient_name": "John Doe",
        "pharmacist_name": "Dr. Smith",
        "items": [
            {
                "batch_id": 3,
                "quantity": 14,
                "dosage_instructions": "1 tablet twice daily after meals"
            }
        ]
    }
    """
    data = request.get_json()
    if not data or not data.get("items"):
        return jsonify({"error": "At least one item is required"}), 400

    with get_session() as session:
        items_data = []
        total_amount = 0.0
        invoice_items = []

        for item in data["items"]:
            batch_id = item.get("batch_id")
            quantity = int(item.get("quantity", 1))

            batch = session.get(InventoryBatch, batch_id)
            if not batch:
                return jsonify({"error": f"Batch ID {batch_id} not found"}), 404
            if batch.status != "active":
                return jsonify({"error": f"Batch {batch.batch_number} is not active"}), 400
            if batch.quantity_remaining < quantity:
                return jsonify({
                    "error": f"Insufficient stock for batch {batch.batch_number}. "
                             f"Available: {batch.quantity_remaining}, Requested: {quantity}"
                }), 400

            med = session.query(Medicine).filter_by(medicine_id=batch.medicine_id).first()
            unit_price = med.unit_price if med else 0.0
            line_total = unit_price * quantity
            total_amount += line_total

            # Deduct stock
            batch.quantity_remaining -= quantity

            inv_item = InvoiceItem(
                batch_id=batch_id,
                medicine_id=batch.medicine_id,
                quantity=quantity,
                unit_price=unit_price,
                dosage_instructions=item.get("dosage_instructions", "As directed by physician"),
            )
            invoice_items.append(inv_item)

            items_data.append({
                "medicine_id": batch.medicine_id,
                "name": med.name if med else "Unknown",
                "generic_name": med.generic_name if med else "",
                "batch": batch.batch_number,
                "expiry": batch.expiry_date.strftime("%Y-%m-%d") if batch.expiry_date else "",
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": round(line_total, 2),
                "dosage": item.get("dosage_instructions", "As directed by physician"),
                "storage": med.storage_instructions if med else "",
                "side_effects_summary": (json.loads(med.side_effects)[:3] if med and med.side_effects else []),
            })

        # Generate invoice number
        count = session.query(Invoice).count()
        invoice_number = f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{count + 1:04d}"

        # Build QR payload
        invoice_data_for_qr = {
            "invoice_number": invoice_number,
            "patient_name": data.get("patient_name", "Patient"),
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "medicines": items_data,
        }

        # Generate QR image
        from services.qr_service import save_qr_image
        qr_bytes, qr_payload_str = generate_invoice_qr(invoice_data_for_qr)
        qr_image_path = save_qr_image(qr_bytes, invoice_number)

        invoice = Invoice(
            invoice_number=invoice_number,
            pharmacist_name=data.get("pharmacist_name", "Pharmacist"),
            patient_name=data.get("patient_name", "Patient"),
            total_amount=round(total_amount, 2),
            qr_payload=qr_payload_str,
            qr_image_path=qr_image_path,
        )
        session.add(invoice)
        session.flush()

        for inv_item in invoice_items:
            inv_item.invoice_id = invoice.id
            session.add(inv_item)

        session.commit()

        return jsonify({
            "message": "Invoice created successfully",
            "invoice_number": invoice_number,
            "total_amount": round(total_amount, 2),
            "qr_image_url": f"/api/billing/{invoice.id}/qr",
            "invoice_id": invoice.id,
            "items": items_data,
        }), 201


# ── List Invoices ─────────────────────────────────────────────────────────────

@billing_bp.get("/api/billing/invoices")
def list_invoices():
    """Return all invoices, most recent first."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("q", "").strip()

    with get_session() as session:
        query = session.query(Invoice)
        if search:
            query = query.filter(
                Invoice.invoice_number.ilike(f"%{search}%") |
                Invoice.patient_name.ilike(f"%{search}%")
            )
        total = query.count()
        invoices = (
            query.order_by(Invoice.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return jsonify({
            "total": total,
            "page": page,
            "per_page": per_page,
            "invoices": [i.to_dict() for i in invoices]
        })


# ── Get Invoice ────────────────────────────────────────────────────────────────

@billing_bp.get("/api/billing/<int:invoice_id>")
def get_invoice(invoice_id):
    """Return invoice details including line items."""
    with get_session() as session:
        inv = session.get(Invoice, invoice_id)
        if not inv:
            return jsonify({"error": "Invoice not found"}), 404
        d = inv.to_dict()
        items = session.query(InvoiceItem).filter_by(invoice_id=invoice_id).all()
        d["items"] = [it.to_dict() for it in items]
        return jsonify(d)


# ── Serve QR Image ─────────────────────────────────────────────────────────────

@billing_bp.get("/api/billing/<int:invoice_id>/qr")
def get_qr_image(invoice_id):
    """Serve the QR code image for an invoice."""
    with get_session() as session:
        inv = session.get(Invoice, invoice_id)
        if not inv or not inv.qr_image_path:
            abort(404)
        if not os.path.exists(inv.qr_image_path):
            abort(404)
        return send_file(inv.qr_image_path, mimetype="image/png")


# ── Decode QR ──────────────────────────────────────────────────────────────────

@billing_bp.post("/api/billing/decode-qr")
def decode_qr():
    """
    Decode a QR payload string (from patient's scan).
    Body: { "payload": "<json string or base64 from QR>" }
    """
    data = request.get_json()
    raw = data.get("payload", "").strip()
    if not raw:
        return jsonify({"error": "No payload provided"}), 400

    result = decode_qr_payload(raw)
    if result.get("status") == "error":
        return jsonify({"error": result.get("message", "Invalid QR code")}), 400

    return jsonify(result)


# ── Available Batches for Billing ─────────────────────────────────────────────

@billing_bp.get("/api/billing/available-stock")
def available_stock():
    """Return active batches available for billing, with medicine info."""
    q = request.args.get("q", "").strip()
    with get_session() as session:
        query = (
            session.query(InventoryBatch, Medicine)
            .join(Medicine, InventoryBatch.medicine_id == Medicine.medicine_id)
            .filter(
                InventoryBatch.status == "active",
                InventoryBatch.quantity_remaining > 0,
            )
        )
        if q:
            query = query.filter(
                Medicine.name.ilike(f"%{q}%") |
                Medicine.generic_name.ilike(f"%{q}%")
            )
        results = query.order_by(Medicine.name).limit(50).all()
        return jsonify([
            {
                **b.to_dict(),
                "medicine_name": m.name,
                "generic_name": m.generic_name,
                "dosage_form": m.dosage_form,
                "strength": m.strength,
                "unit_price": m.unit_price,
                "category": m.category,
            }
            for b, m in results
        ])
