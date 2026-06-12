import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.base import SessionLocal
from database.models import Medicine, InventoryBatch, Invoice, InvoiceItem, SalesLog, Reminder, Alert

db = SessionLocal()
try:
    print("Clearing data...")
    db.query(Reminder).delete()
    db.query(Alert).delete()
    db.query(InvoiceItem).delete()
    db.query(Invoice).delete()
    db.query(SalesLog).delete()
    db.query(InventoryBatch).delete()
    db.query(Medicine).delete()
    db.commit()
    print("All inventory, sales, and billing data has been cleared!")
except Exception as e:
    db.rollback()
    print(f"Failed: {e}")
finally:
    db.close()
