"""
Seed the MedTrack database with sample medicines and inventory batches.
Run once:  python seed_database.py
"""

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config
from database.db import init_db, get_session, shutdown_session
from database.models import Medicine, InventoryBatch

SUPPLIERS = [
    "National Drug Distributors",
    "MedLine Wholesale",
    "PharmaExpress Logistics",
    "Apollo Supply Chain",
    "HealthCare Direct",
]


def seed_medicines(session):
    """Load medicines from knowledge base JSON into the database."""
    kb_path = config.KNOWLEDGE_BASE_PATH
    if not kb_path.exists():
        print(f"[ERROR] Knowledge base not found at {kb_path}")
        return []

    with open(kb_path, "r", encoding="utf-8") as f:
        medicines_data = json.load(f)

    added = []
    for med in medicines_data:
        existing = session.query(Medicine).filter_by(medicine_id=med["medicine_id"]).first()
        if existing:
            continue

        m = Medicine(
            medicine_id=med["medicine_id"],
            name=med["name"],
            generic_name=med.get("generic_name"),
            category=med.get("category"),
            manufacturer=med.get("manufacturer"),
            dosage_form=med.get("dosage_form"),
            strength=med.get("strength"),
            description=med.get("description"),
            side_effects=med.get("side_effects"),
            interactions=med.get("interactions"),
            contraindications=med.get("contraindications"),
            storage_instructions=med.get("storage_instructions"),
            dosage_schedule=med.get("dosage_schedule"),
            missed_dose_guidance=med.get("missed_dose_guidance"),
            unit_price=med.get("unit_price", 0.0),
        )
        session.add(m)
        added.append(med["medicine_id"])

    session.commit()
    print(f"[OK] Seeded {len(added)} medicines ({len(medicines_data) - len(added)} already existed)")
    return medicines_data


def seed_inventory(session, medicines_data):
    """Create sample inventory batches for each medicine."""
    now = datetime.now(timezone.utc)
    added = 0

    for med in medicines_data:
        med_id = med["medicine_id"]

        # Check if batches already exist for this medicine
        existing_count = session.query(InventoryBatch).filter_by(medicine_id=med_id).count()
        if existing_count > 0:
            continue

        # Create 2–3 batches per medicine with varying states
        num_batches = random.randint(2, 3)
        for i in range(num_batches):
            # Manufacture date: 1–18 months ago
            mfg_offset = random.randint(30, 540)
            manufacture_date = now - timedelta(days=mfg_offset)

            # Expiry scenarios:
            #   Batch 0: normal (6–24 months from now)
            #   Batch 1: near-expiry (5–35 days from now) — triggers alerts
            #   Batch 2: already expired (for demo)
            if i == 0:
                expiry_offset = random.randint(180, 730)
                expiry_date = now + timedelta(days=expiry_offset)
                qty_remaining = random.randint(30, 200)
                status = "active"
            elif i == 1:
                expiry_offset = random.randint(5, 35)
                expiry_date = now + timedelta(days=expiry_offset)
                qty_remaining = random.randint(2, 15)  # low stock too
                status = "active"
            else:
                expiry_offset = random.randint(1, 30)
                expiry_date = now - timedelta(days=expiry_offset)
                qty_remaining = random.randint(0, 5)
                status = "expired"

            qty_received = qty_remaining + random.randint(10, 50)
            batch_num = f"BATCH-{med_id[-3:]}-{2026}-{chr(65 + i)}{random.randint(100, 999)}"
            received_days_ago = random.randint(1, mfg_offset)

            batch = InventoryBatch(
                medicine_id=med_id,
                batch_number=batch_num,
                manufacture_date=manufacture_date,
                expiry_date=expiry_date,
                quantity_received=qty_received,
                quantity_remaining=qty_remaining,
                supplier=random.choice(SUPPLIERS),
                received_at=now - timedelta(days=received_days_ago),
                manufacturer_qr_data=json.dumps({
                    "manufacturer": med.get("manufacturer", "Unknown"),
                    "batch": batch_num,
                    "medicine": med["name"],
                    "mfg_date": manufacture_date.strftime("%Y-%m-%d"),
                    "exp_date": expiry_date.strftime("%Y-%m-%d"),
                }),
                status=status,
            )
            session.add(batch)
            added += 1

    session.commit()
    print(f"[OK] Seeded {added} inventory batches")


def main():
    print("=" * 50)
    print("  MedTrack Database Seeder")
    print("=" * 50)

    init_db()
    session = get_session()

    try:
        medicines_data = seed_medicines(session)
        if medicines_data:
            seed_inventory(session, medicines_data)
        print("\n[DONE] Database ready at:", config.DATABASE_URL)
    except Exception as e:
        session.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        shutdown_session()


if __name__ == "__main__":
    main()
