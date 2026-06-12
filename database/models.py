"""
SQLAlchemy ORM models for MedTrack.

Tables
------
- Medicine        : master catalogue of medicines
- InventoryBatch  : per-batch stock tracking
- Invoice         : sales / billing records
- InvoiceItem     : line-items per invoice
- Alert           : proactive system alerts
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ── Medicine Catalogue ───────────────────────────────────────────────────────

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    medicine_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    generic_name = Column(String(200))
    category = Column(String(100))           # e.g. "Antibiotic", "Analgesic"
    manufacturer = Column(String(200))
    dosage_form = Column(String(100))        # e.g. "Tablet", "Capsule", "Syrup"
    strength = Column(String(100))           # e.g. "500mg", "250mg/5ml"
    description = Column(Text)
    side_effects = Column(Text)              # JSON-serialised list
    interactions = Column(Text)              # drug-drug & food-drug interactions
    contraindications = Column(Text)
    storage_instructions = Column(String(300))
    dosage_schedule = Column(Text)           # standard dosing guidance
    missed_dose_guidance = Column(Text)
    unit_price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    batches = relationship("InventoryBatch", back_populates="medicine", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "medicine_id": self.medicine_id,
            "name": self.name,
            "generic_name": self.generic_name,
            "category": self.category,
            "manufacturer": self.manufacturer,
            "dosage_form": self.dosage_form,
            "strength": self.strength,
            "description": self.description,
            "side_effects": self.side_effects,
            "interactions": self.interactions,
            "contraindications": self.contraindications,
            "storage_instructions": self.storage_instructions,
            "dosage_schedule": self.dosage_schedule,
            "missed_dose_guidance": self.missed_dose_guidance,
            "unit_price": self.unit_price,
        }


# ── Inventory Batches ────────────────────────────────────────────────────────

class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    medicine_id = Column(String(20), ForeignKey("medicines.medicine_id"), nullable=False, index=True)
    batch_number = Column(String(50), unique=True, nullable=False)
    manufacture_date = Column(DateTime)
    expiry_date = Column(DateTime, nullable=False)
    quantity_received = Column(Integer, nullable=False, default=0)
    quantity_remaining = Column(Integer, nullable=False, default=0)
    supplier = Column(String(200))
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    manufacturer_qr_data = Column(Text)      # raw QR payload from manufacturer
    status = Column(
        String(20), default="active"         # active | expired | recalled
    )

    # Relationships
    medicine = relationship("Medicine", back_populates="batches")
    alerts = relationship("Alert", back_populates="batch", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "medicine_id": self.medicine_id,
            "batch_number": self.batch_number,
            "medicine_name": self.medicine.name if self.medicine else None,
            "manufacture_date": self.manufacture_date.isoformat() if self.manufacture_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "quantity_received": self.quantity_received,
            "quantity_remaining": self.quantity_remaining,
            "supplier": self.supplier,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "status": self.status,
        }


# ── Invoices ─────────────────────────────────────────────────────────────────

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(30), unique=True, nullable=False)
    pharmacist_name = Column(String(200), default="Pharmacist")
    patient_name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_amount = Column(Float, default=0.0)
    qr_payload = Column(Text)                # JSON-encoded QR data
    qr_image_path = Column(String(500))      # path to generated QR PNG

    # Relationships
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "pharmacist_name": self.pharmacist_name,
            "patient_name": self.patient_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "total_amount": self.total_amount,
            "items": [item.to_dict() for item in self.items],
        }


# ── Invoice Line Items ───────────────────────────────────────────────────────

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id"), nullable=False)
    medicine_id = Column(String(20), ForeignKey("medicines.medicine_id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, default=0.0)
    dosage_instructions = Column(Text)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    batch = relationship("InventoryBatch")
    medicine = relationship("Medicine")

    def to_dict(self):
        return {
            "id": self.id,
            "medicine_id": self.medicine_id,
            "medicine_name": self.medicine.name if self.medicine else None,
            "batch_number": self.batch.batch_number if self.batch else None,
            "expiry_date": self.batch.expiry_date.isoformat() if self.batch and self.batch.expiry_date else None,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "dosage_instructions": self.dosage_instructions,
        }


# ── System Alerts ────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(
        String(30), nullable=False           # low_stock | expiry_warning | expired | counterfeit_risk
    )
    batch_id = Column(Integer, ForeignKey("inventory_batches.id"), nullable=True)
    medicine_id = Column(String(20), nullable=True)
    message = Column(Text, nullable=False)
    severity = Column(
        String(20), default="info"           # info | warning | critical
    )
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    batch = relationship("InventoryBatch", back_populates="alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "alert_type": self.alert_type,
            "batch_id": self.batch_id,
            "medicine_id": self.medicine_id,
            "message": self.message,
            "severity": self.severity,
            "is_resolved": self.is_resolved,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
