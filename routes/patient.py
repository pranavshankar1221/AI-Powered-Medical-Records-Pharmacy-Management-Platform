"""
routes/patient.py
B2C Patient Companion Routes – decoding billing QR, loading digital cabinet,
and guardrailed RAG chatbot queries.
"""

from flask import Blueprint, request, jsonify
import json
from services.rag_engine import generate_response
from services.qr_service import decode_qr_payload
from database.db import get_session
from database.models import InventoryBatch, Medicine

patient_bp = Blueprint("patient", __name__)


# ── Decode & Verify Receipt QR ────────────────────────────────────────────────

@patient_bp.post("/api/patient/scan")
def patient_scan_qr():
    """
    Scan a QR code payload from a printed receipt.
    Verifies signature and returns the list of medicines to add to cabinet.
    """
    data = request.get_json()
    payload = data.get("payload", "").strip()

    if not payload:
        return jsonify({"error": "No QR payload provided"}), 400

    result = decode_qr_payload(payload)
    if result.get("status") == "error":
        return jsonify({"error": result.get("message", "Invalid QR code")}), 400

    # Double check batches in DB for authentic tracking status
    with get_session() as session:
        for med in result.get("medicines", []):
            batch_num = med.get("batch")
            med_id = med.get("medicine_id")
            
            # Find batch in database to confirm status
            batch = session.query(InventoryBatch).filter_by(
                batch_number=batch_num,
                medicine_id=med_id
            ).first()
            
            if batch:
                med["db_status"] = batch.status
                med["batch_exists"] = True
                # If database marks the batch as recalled or expired, alert patient
                if batch.status == "recalled":
                    med["authenticity_alert"] = "RECALLED: This batch has been recalled by manufacturer!"
                elif batch.status == "expired":
                    med["authenticity_alert"] = "EXPIRED: This medicine batch has expired!"
                else:
                    med["authenticity_alert"] = None
            else:
                med["db_status"] = "unknown"
                med["batch_exists"] = False
                med["authenticity_alert"] = "UNVERIFIED: Batch not found in official pharmacy database."

    return jsonify({
        "success": True,
        "verified": result.get("verified", False),
        "cabinet_data": result
    })


# ── AI Patient Companion Chatbot ──────────────────────────────────────────────

@patient_bp.post("/api/patient/chat")
def patient_chat():
    """
    Chat endpoint for patient. Scopes questions to scanned cabinet medicines.
    Body:
    {
        "query": "Can I take this with milk?",
        "medicine_ids": ["MED_001", "MED_002"],
        "cabinet_medicines": [{"name": "Amoxicillin 500mg", "medicine_id": "MED_001"}]
    }
    """
    data = request.get_json()
    if not data or not data.get("query"):
        return jsonify({"error": "Query is required"}), 400

    query = data["query"]
    medicine_ids = data.get("medicine_ids", [])
    patient_medicines = data.get("cabinet_medicines", [])

    # Run RAG Generation
    response = generate_response(
        query=query,
        medicine_ids=medicine_ids,
        patient_medicines=patient_medicines
    )

    # Log/track via MLOps monitor if available
    try:
        from mlops.monitor import log_inference
        log_inference(
            query=query,
            medicine_ids=medicine_ids,
            response=response["answer"],
            sources=response["sources"],
            latency_ms=response["latency_ms"],
            model=response.get("model", "unknown")
        )
    except Exception as e:
        print(f"MLOps monitoring error: {e}")

    return jsonify(response)


# ── Medicine Schedule/Calendar Generator ─────────────────────────────────────

@patient_bp.post("/api/patient/calendar")
def generate_calendar():
    """
    Generate a formatted weekly/daily schedule for a set of cabinet medicines.
    Accepts cabinet medicines JSON array and parses standard dosage schedules into times.
    """
    data = request.get_json()
    medicines = data.get("medicines", [])
    
    schedule = {
        "morning": [],    # e.g., 08:00
        "afternoon": [],  # e.g., 13:00
        "evening": [],    # e.g., 18:00
        "night": []       # e.g., 21:00
    }

    for med in medicines:
        dosage_text = med.get("dosage", "").lower()
        med_name = med.get("name", "Medicine")
        instructions = med.get("dosage", "As directed")

        # Basic text-parsing rules to allocate slots
        if "morning" in dosage_text or "qd" in dosage_text or "once daily" in dosage_text or "1x daily" in dosage_text:
            schedule["morning"].append({"name": med_name, "instructions": instructions})
        
        if "twice daily" in dosage_text or "2x daily" in dosage_text or "bid" in dosage_text:
            schedule["morning"].append({"name": med_name, "instructions": instructions})
            schedule["evening"].append({"name": med_name, "instructions": instructions})
            
        if "three times" in dosage_text or "3x daily" in dosage_text or "tid" in dosage_text:
            schedule["morning"].append({"name": med_name, "instructions": instructions})
            schedule["afternoon"].append({"name": med_name, "instructions": instructions})
            schedule["evening"].append({"name": med_name, "instructions": instructions})

        if "four times" in dosage_text or "4x daily" in dosage_text or "qid" in dosage_text:
            schedule["morning"].append({"name": med_name, "instructions": instructions})
            schedule["afternoon"].append({"name": med_name, "instructions": instructions})
            schedule["evening"].append({"name": med_name, "instructions": instructions})
            schedule["night"].append({"name": med_name, "instructions": instructions})

        if "night" in dosage_text or "bedtime" in dosage_text or "hs" in dosage_text:
            schedule["night"].append({"name": med_name, "instructions": instructions})

        # Default fallback if no pattern matched
        if not any(slot for slot in schedule.values() if any(item["name"] == med_name for item in slot)):
            schedule["morning"].append({"name": med_name, "instructions": instructions})

    return jsonify({"schedule": schedule})
