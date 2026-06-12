"""
QR Code generation and bill token management.
QR codes contain ONLY the bill_token — never patient data or medicine info.
"""

import hashlib
import hmac
import uuid
import json
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H

import config


def generate_bill_token() -> str:
    """Generate a cryptographically unique bill token."""
    raw = str(uuid.uuid4())
    signature = hmac.new(
        config.QR_HMAC_SECRET.encode(),
        raw.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"MQ-{signature.upper()}"


def generate_qr_code(bill_token: str) -> str:
    """
    Generate a QR code image containing ONLY the bill_token.
    Returns the relative file path of the saved QR image.
    """
    qr = qrcode.QRCode(
        version=2,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    # The URL allows patients to scan it with their phone camera and be directed to the tracker
    # with the token pre-filled.
    frontend_url = getattr(config, "FRONTEND_URL", "http://localhost:5174")
    qr.add_data(f"{frontend_url}/patient/reminders?token={bill_token}")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    filename = f"{bill_token}.png"
    filepath = config.QR_DIR / filename
    img.save(str(filepath))

    return f"qr_codes/{filename}"


def verify_bill_token(token: str) -> bool:
    """Basic format validation of a bill token."""
    return token.startswith("MQ-") and len(token) == 19
