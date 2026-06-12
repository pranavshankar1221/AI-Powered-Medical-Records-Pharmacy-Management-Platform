"""
SQLAlchemy ORM models for MEDIQR MLOPS.

Tables:
- User            : authentication & role management
- Medicine        : master catalogue of medicines
- InventoryBatch  : per-batch stock tracking
- Invoice         : sales / billing records
- InvoiceItem     : line-items per invoice
- Reminder        : patient medicine reminders
- Alert           : proactive system alerts
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Date, Time
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ── Users & Authentication ───────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(300), nullable=False)
    full_name = Column(String(200), default="")
    phone = Column(String(20), default="")
    role = Column(String(20), nullable=False, default="patient")  # admin | pharmacist | patient
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Medicine Catalogue ───────────────────────────────────────────────────────

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    medicine_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    generic_name = Column(String(200))
    category = Column(String(100))
    manufacturer = Column(String(200))
    dosage_form = Column(String(100))
    strength = Column(String(100))
    description = Column(Text)
    purpose = Column(Text)
    side_effects = Column(Text)
    interactions = Column(Text)
    contraindications = Column(Text)
    storage_instructions = Column(String(300))
    dosage_schedule = Column(Text)
    food_instructions = Column(Text)
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
            "purpose": self.purpose,
            "side_effects": self.side_effects,
            "interactions": self.interactions,
            "contraindications": self.contraindications,
            "storage_instructions": self.storage_instructions,
            "dosage_schedule": self.dosage_schedule,
            "food_instructions": self.food_instructions,
            "missed_dose_guidance": self.missed_dose_guidance,
            "unit_price": self.unit_price,
            "created_at": self.created_at.isoformat() if self.created_at else None,
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
    status = Column(String(20), default="active")  # active | expired | recalled

    # Relationships
    medicine = relationship("Medicine", back_populates="batches")
    alerts = relationship("Alert", back_populates="batch", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "medicine_id": self.medicine_id,
            "batch_number": self.batch_number,
            "medicine_name": self.medicine.name if self.medicine else None,
            "category": self.medicine.category if self.medicine else None,
            "manufacturer": self.medicine.manufacturer if self.medicine else None,
            "manufacture_date": self.manufacture_date.isoformat() if self.manufacture_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "quantity_received": self.quantity_received,
            "quantity_remaining": self.quantity_remaining,
            "supplier": self.supplier,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "status": self.status,
            "unit_price": self.medicine.unit_price if self.medicine else 0,
        }


# ── Invoices ─────────────────────────────────────────────────────────────────

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(30), unique=True, nullable=False)
    bill_token = Column(String(100), unique=True, nullable=False, index=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    patient_name = Column(String(200), nullable=False)
    patient_phone = Column(String(20), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_amount = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    final_amount = Column(Float, default=0.0)
    qr_image_path = Column(String(500))

    # Relationships
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    pharmacist = relationship("User", foreign_keys=[pharmacist_id])

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "bill_token": self.bill_token,
            "pharmacist_name": self.pharmacist.full_name if self.pharmacist else "Staff",
            "patient_name": self.patient_name,
            "patient_phone": self.patient_phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "total_amount": self.total_amount,
            "discount": self.discount,
            "tax": self.tax,
            "final_amount": self.final_amount,
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
    subtotal = Column(Float, default=0.0)
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
            "subtotal": self.subtotal,
            "dosage_instructions": self.dosage_instructions,
            "purpose": self.medicine.purpose if self.medicine else None,
            "side_effects": self.medicine.side_effects if self.medicine else None,
            "food_instructions": self.medicine.food_instructions if self.medicine else None,
            "manufacturer": self.medicine.manufacturer if self.medicine else None,
        }


# ── Medicine Reminders ───────────────────────────────────────────────────────

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medicine_name = Column(String(200), nullable=False)
    dosage = Column(String(100), default="")
    time_of_day = Column(String(20), default="morning")  # morning | afternoon | night | custom
    custom_time = Column(Time, nullable=True)
    status = Column(String(20), default="pending")  # taken | pending | missed
    scheduled_date = Column(Date, nullable=True)
    notes = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="reminders")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "medicine_name": self.medicine_name,
            "dosage": self.dosage,
            "time_of_day": self.time_of_day,
            "custom_time": self.custom_time.isoformat() if self.custom_time else None,
            "status": self.status,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── System Alerts ────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(30), nullable=False)  # low_stock | expiry_warning | expired
    batch_id = Column(Integer, ForeignKey("inventory_batches.id"), nullable=True)
    medicine_id = Column(String(20), nullable=True)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")  # info | warning | critical
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


# ── Sales Log (for ML pipeline) ─────────────────────────────────────────────

class SalesLog(Base):
    __tablename__ = "sales_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    medicine_id = Column(String(20), ForeignKey("medicines.medicine_id"), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    sale_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    month = Column(Integer)
    year = Column(Integer)
    revenue = Column(Float, default=0.0)

    medicine = relationship("Medicine")

    def to_dict(self):
        return {
            "id": self.id,
            "medicine_id": self.medicine_id,
            "medicine_name": self.medicine.name if self.medicine else None,
            "quantity_sold": self.quantity_sold,
            "sale_date": self.sale_date.isoformat() if self.sale_date else None,
            "month": self.month,
            "year": self.year,
            "revenue": self.revenue,
        }
