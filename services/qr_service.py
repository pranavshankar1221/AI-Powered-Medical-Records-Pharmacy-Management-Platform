"""
QR Code generation and verification service.
Generates dynamic QR codes for invoices with HMAC signatures for anti-counterfeit protection.
"""

import hashlib
import hmac
import io
import json
import os
from datetime import datetime, timezone

import qrcode
from qrcode.constants import ERROR_CORRECT_H

import config


def generate_invoice_qr(invoice_data: dict) -> tuple[bytes, str]:
    """
    Generate a QR code for an invoice payload.
    
    Args:
        invoice_data: dict containing invoice details and medicine list
        
    Returns:
        tuple of (qr_image_bytes, qr_payload_json_string)
    """
    # Build the QR payload
    payload = {
        "invoice_id": invoice_data["invoice_number"],
        "pharmacy": config.PHARMACY_NAME,
        "date": invoice_data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "patient": invoice_data.get("patient_name", ""),
        "medicines": invoice_data.get("medicines", []),
    }

    # Create HMAC signature for anti-counterfeit verification
    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    signature = hmac.new(
        config.QR_HMAC_SECRET.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    payload["signature"] = signature
    final_payload = json.dumps(payload, separators=(",", ":"))

    # Generate QR code image
    qr = qrcode.QRCode(
        version=None,  # auto-size
        error_correction=ERROR_CORRECT_H,
        box_size=8,
        border=4,
    )
    qr.add_data(final_payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0a0e27", back_color="white")

    # Save to bytes (PNG format)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_bytes = buffer.getvalue()
    # qr_service.py
    # lines 55-70

    return qr_bytes, final_payload


def save_qr_image(qr_bytes: bytes, invoice_number: str) -> str:
    """Save QR code image to disk and return the file path."""
    filename = f"qr_{invoice_number}.png"
    filepath = os.path.join(str(config.QR_DIR), filename)
    with open(filepath, "wb") as f:
        f.write(qr_bytes)
    return filepath


def verify_qr_payload(payload_json: str) -> tuple[bool, dict]:
    """
    Verify a QR payload's HMAC signature.
    
    Args:
        payload_json: JSON string from scanned QR code
        
    Returns:
        tuple of (is_verified, payload_dict)
    """
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError:
        return False, {"error": "Invalid QR data — not valid JSON"}

    received_signature = payload.pop("signature", None)
    if not received_signature:
        return False, {"error": "No signature found — QR may be tampered with"}

    # Recompute the signature
    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    expected_signature = hmac.new(
        config.QR_HMAC_SECRET.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if hmac.compare_digest(received_signature, expected_signature):
        payload["verified"] = True
        payload["signature"] = received_signature
        return True, payload
    else:
        payload["verified"] = False
        return False, {"error": "Signature mismatch — QR data may have been tampered with"}


def decode_qr_payload(payload_json: str) -> dict:
    """
    Decode and verify a QR payload, returning the full medicine list
    with verification status.
    """
    is_verified, payload = verify_qr_payload(payload_json)

    if not is_verified:
        return {
            "status": "error",
            "verified": False,
            "message": payload.get("error", "Verification failed"),
        }

    return {
        "status": "success",
        "verified": True,
        "invoice_id": payload.get("invoice_id"),
        "pharmacy": payload.get("pharmacy"),
        "date": payload.get("date"),
        "patient": payload.get("patient"),
        "medicines": payload.get("medicines", []),
    }
