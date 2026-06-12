"""
Seed database with demo data — admin, pharmacist, patient users + medicines + batches + sales history.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import random

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.base import SessionLocal, init_db
from database.models import User, Medicine, InventoryBatch, Invoice, InvoiceItem, SalesLog
from utils.security import hash_password
from services.qr_service import generate_bill_token, generate_qr_code


def seed():
    """Populate the database with demo data."""
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already has data. Skipping seed.")
            return

        print("🌱 Seeding database...")

        # ── Users ────────────────────────────────────────────────────────
        users = [
            User(username="admin", email="admin@mediqr.com",
                 hashed_password=hash_password("admin123"),
                 full_name="System Administrator", role="admin", phone="+91-9876543210"),
            User(username="pharmacist1", email="pharma1@mediqr.com",
                 hashed_password=hash_password("pharma123"),
                 full_name="Dr. Rajesh Kumar", role="pharmacist", phone="+91-9876543211"),
            User(username="pharmacist2", email="pharma2@mediqr.com",
                 hashed_password=hash_password("pharma123"),
                 full_name="Dr. Priya Sharma", role="pharmacist", phone="+91-9876543212"),
            User(username="patient1", email="patient1@mediqr.com",
                 hashed_password=hash_password("patient123"),
                 full_name="Amit Patel", role="patient", phone="+91-9876543213"),
            User(username="patient2", email="patient2@mediqr.com",
                 hashed_password=hash_password("patient123"),
                 full_name="Sneha Reddy", role="patient", phone="+91-9876543214"),
        ]
        db.add_all(users)
        db.flush()
        print(f"  ✅ Created {len(users)} users")

        # ── Medicines ────────────────────────────────────────────────────
        medicines_data = [
            {"medicine_id": "MED-001", "name": "Paracetamol 500mg", "generic_name": "Acetaminophen",
             "category": "Antipyretic", "manufacturer": "Cipla Ltd", "dosage_form": "Tablet",
             "strength": "500mg", "unit_price": 2.50,
             "purpose": "Fever and mild pain relief",
             "description": "Common analgesic and antipyretic used for fever and pain",
             "side_effects": "Nausea, rash (rare), liver issues with overdose",
             "food_instructions": "Can be taken with or without food",
             "dosage_schedule": "1-2 tablets every 4-6 hours as needed, max 8 tablets/day"},
            {"medicine_id": "MED-002", "name": "Amoxicillin 250mg", "generic_name": "Amoxicillin",
             "category": "Antibiotic", "manufacturer": "Sun Pharma", "dosage_form": "Capsule",
             "strength": "250mg", "unit_price": 8.00,
             "purpose": "Bacterial infections",
             "description": "Broad-spectrum antibiotic for various bacterial infections",
             "side_effects": "Diarrhea, nausea, skin rash",
             "food_instructions": "Take with food to reduce stomach upset",
             "dosage_schedule": "1 capsule 3 times daily for 5-7 days"},
            {"medicine_id": "MED-003", "name": "Cetirizine 10mg", "generic_name": "Cetirizine",
             "category": "Antihistamine", "manufacturer": "Dr. Reddy's", "dosage_form": "Tablet",
             "strength": "10mg", "unit_price": 3.00,
             "purpose": "Allergy relief",
             "description": "Second-generation antihistamine for allergies",
             "side_effects": "Drowsiness, dry mouth, headache",
             "food_instructions": "Can be taken with or without food",
             "dosage_schedule": "1 tablet once daily"},
            {"medicine_id": "MED-004", "name": "Omeprazole 20mg", "generic_name": "Omeprazole",
             "category": "Antacid", "manufacturer": "Lupin Ltd", "dosage_form": "Capsule",
             "strength": "20mg", "unit_price": 5.50,
             "purpose": "Acid reflux and ulcers",
             "description": "Proton pump inhibitor for acid-related disorders",
             "side_effects": "Headache, abdominal pain, nausea",
             "food_instructions": "Take 30 minutes before breakfast",
             "dosage_schedule": "1 capsule once daily before breakfast"},
            {"medicine_id": "MED-005", "name": "Ibuprofen 400mg", "generic_name": "Ibuprofen",
             "category": "Anti-inflammatory", "manufacturer": "Abbott India", "dosage_form": "Tablet",
             "strength": "400mg", "unit_price": 4.00,
             "purpose": "Pain, inflammation, and fever",
             "description": "NSAID for pain relief and anti-inflammatory action",
             "side_effects": "Stomach upset, dizziness, heartburn",
             "food_instructions": "Take with food or milk",
             "dosage_schedule": "1 tablet every 6-8 hours as needed"},
            {"medicine_id": "MED-006", "name": "Metformin 500mg", "generic_name": "Metformin",
             "category": "Antidiabetic", "manufacturer": "USV Ltd", "dosage_form": "Tablet",
             "strength": "500mg", "unit_price": 3.50,
             "purpose": "Type 2 diabetes management",
             "description": "First-line medication for type 2 diabetes",
             "side_effects": "Nausea, diarrhea, stomach cramps",
             "food_instructions": "Take with meals",
             "dosage_schedule": "1 tablet twice daily with meals"},
            {"medicine_id": "MED-007", "name": "Amlodipine 5mg", "generic_name": "Amlodipine",
             "category": "Antihypertensive", "manufacturer": "Pfizer", "dosage_form": "Tablet",
             "strength": "5mg", "unit_price": 6.00,
             "purpose": "High blood pressure management",
             "description": "Calcium channel blocker for hypertension",
             "side_effects": "Ankle swelling, headache, flushing",
             "food_instructions": "Can be taken with or without food",
             "dosage_schedule": "1 tablet once daily"},
            {"medicine_id": "MED-008", "name": "Azithromycin 500mg", "generic_name": "Azithromycin",
             "category": "Antibiotic", "manufacturer": "Zydus Cadila", "dosage_form": "Tablet",
             "strength": "500mg", "unit_price": 15.00,
             "purpose": "Bacterial infections",
             "description": "Macrolide antibiotic for respiratory and skin infections",
             "side_effects": "Diarrhea, nausea, abdominal pain",
             "food_instructions": "Take on empty stomach, 1 hour before meals",
             "dosage_schedule": "1 tablet once daily for 3 days"},
            {"medicine_id": "MED-009", "name": "Vitamin D3 1000IU", "generic_name": "Cholecalciferol",
             "category": "Vitamin", "manufacturer": "Sanofi India", "dosage_form": "Tablet",
             "strength": "1000IU", "unit_price": 5.00,
             "purpose": "Vitamin D supplementation",
             "description": "Vitamin D supplement for bone health",
             "side_effects": "Generally well tolerated; excess may cause hypercalcemia",
             "food_instructions": "Take with a fatty meal for better absorption",
             "dosage_schedule": "1 tablet once daily"},
            {"medicine_id": "MED-010", "name": "Salbutamol Inhaler", "generic_name": "Salbutamol",
             "category": "Bronchodilator", "manufacturer": "Cipla Ltd", "dosage_form": "Inhaler",
             "strength": "100mcg/puff", "unit_price": 120.00,
             "purpose": "Asthma and breathing difficulties",
             "description": "Short-acting bronchodilator for asthma relief",
             "side_effects": "Tremor, headache, rapid heartbeat",
             "food_instructions": "N/A - inhaler",
             "dosage_schedule": "1-2 puffs as needed, max 8 puffs/day"},
        ]

        for md in medicines_data:
            db.add(Medicine(**md))
        db.flush()
        print(f"  ✅ Created {len(medicines_data)} medicines")

        # ── Inventory Batches ────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        batches = []
        for i, md in enumerate(medicines_data):
            # Active batch with good stock
            b1 = InventoryBatch(
                medicine_id=md["medicine_id"],
                batch_number=f"BATCH-{md['medicine_id']}-A",
                manufacture_date=now - timedelta(days=random.randint(30, 180)),
                expiry_date=now + timedelta(days=random.randint(180, 730)),
                quantity_received=random.randint(100, 500),
                quantity_remaining=random.randint(50, 300),
                supplier=f"Supplier-{chr(65 + i % 5)}",
            )
            batches.append(b1)

            # Some with low stock
            if i % 3 == 0:
                b2 = InventoryBatch(
                    medicine_id=md["medicine_id"],
                    batch_number=f"BATCH-{md['medicine_id']}-B",
                    manufacture_date=now - timedelta(days=random.randint(60, 200)),
                    expiry_date=now + timedelta(days=random.randint(15, 45)),  # Near expiry
                    quantity_received=50,
                    quantity_remaining=random.randint(2, 8),  # Low stock
                    supplier=f"Supplier-{chr(65 + i % 5)}",
                )
                batches.append(b2)

            # Some expired
            if i % 5 == 0:
                b3 = InventoryBatch(
                    medicine_id=md["medicine_id"],
                    batch_number=f"BATCH-{md['medicine_id']}-EXP",
                    manufacture_date=now - timedelta(days=400),
                    expiry_date=now - timedelta(days=random.randint(1, 30)),  # Expired
                    quantity_received=100,
                    quantity_remaining=random.randint(10, 50),
                    supplier=f"Supplier-{chr(65 + i % 5)}",
                    status="expired",
                )
                batches.append(b3)

        db.add_all(batches)
        db.flush()
        print(f"  ✅ Created {len(batches)} inventory batches")

        # ── Sales History ────────────────────────────────────────────────
        sales = []
        for month_offset in range(12):
            for md in medicines_data:
                qty = random.randint(5, 80)
                sale_date = now - timedelta(days=month_offset * 30 + random.randint(0, 29))
                sales.append(SalesLog(
                    medicine_id=md["medicine_id"],
                    quantity_sold=qty,
                    sale_date=sale_date,
                    month=sale_date.month,
                    year=sale_date.year,
                    revenue=round(qty * md["unit_price"], 2),
                ))
        db.add_all(sales)
        db.flush()
        print(f"  ✅ Created {len(sales)} sales log entries")

        # ── Sample Invoices ──────────────────────────────────────────────
        active_batches = [b for b in batches if b.status == "active"]
        for inv_i in range(5):
            bill_token = generate_bill_token()
            try:
                qr_path = generate_qr_code(bill_token)
            except Exception:
                qr_path = ""

            items_count = random.randint(1, 3)
            selected = random.sample(active_batches[:8], min(items_count, len(active_batches[:8])))

            total = 0
            inv_items = []
            for batch in selected:
                med = db.query(Medicine).filter(Medicine.medicine_id == batch.medicine_id).first()
                qty = random.randint(1, 5)
                subtotal = round(med.unit_price * qty, 2)
                total += subtotal
                inv_items.append(InvoiceItem(
                    batch_id=batch.id,
                    medicine_id=batch.medicine_id,
                    quantity=qty,
                    unit_price=med.unit_price,
                    subtotal=subtotal,
                    dosage_instructions=med.dosage_schedule or "",
                ))

            tax = round(total * 0.05, 2)
            invoice = Invoice(
                invoice_number=f"INV-DEMO-{inv_i + 1:04d}",
                bill_token=bill_token,
                pharmacist_id=users[1].id,
                patient_name=random.choice(["Amit Patel", "Sneha Reddy", "Rahul Singh", "Priya Nair"]),
                total_amount=round(total, 2),
                tax=tax,
                final_amount=round(total + tax, 2),
                qr_image_path=qr_path,
                created_at=now - timedelta(days=random.randint(0, 30)),
            )
            db.add(invoice)
            db.flush()

            for item in inv_items:
                item.invoice_id = invoice.id
                db.add(item)

        db.commit()
        print(f"  ✅ Created 5 sample invoices with QR codes")

        print("\n✅ Database seeded successfully!")
        print("\n📋 Demo Credentials:")
        print("  Admin:      admin / admin123")
        print("  Pharmacist: pharmacist1 / pharma123")
        print("  Patient:    patient1 / patient123")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
