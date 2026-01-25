from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from database import Base

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=func.now())
    total = Column(Float, nullable=False)
    vendor = Column(String, index=True)
    description = Column(Text)


# Invoice Automation Models

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    builder_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    uploaded_at = Column(DateTime, server_default=func.now())
    status = Column(String(50), default='uploaded', index=True)
    processing_method = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    extracted_fields = relationship("ExtractedField", back_populates="invoice", cascade="all, delete-orphan")
    line_items = relationship("LineItem", back_populates="invoice", cascade="all, delete-orphan")
    vendor_matches = relationship("VendorMatch", back_populates="invoice", cascade="all, delete-orphan")
    processing_metrics = relationship("ProcessingMetric", back_populates="invoice", cascade="all, delete-orphan")
    correction_history = relationship("CorrectionHistory", back_populates="invoice", cascade="all, delete-orphan")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    vendor_name = Column(String(255), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    invoice_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=True)
    confidence = Column(Numeric(3, 2), nullable=True)
    raw_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="extracted_fields")


class Subcontractor(Base):
    __tablename__ = "subcontractors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    builder_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    contact_info = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    vendor_matches = relationship("VendorMatch", back_populates="subcontractor")


class VendorMatch(Base):
    __tablename__ = "vendor_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    subcontractor_id = Column(UUID(as_uuid=True), ForeignKey('subcontractors.id'), nullable=True)
    match_score = Column(Integer, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="vendor_matches")
    subcontractor = relationship("Subcontractor", back_populates="vendor_matches")


class CostCode(Base):
    __tablename__ = "cost_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    builder_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 2), nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    suggested_code = Column(String(50), nullable=True)
    confidence = Column(Numeric(3, 2), nullable=True)
    confirmed_code = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")


class CorrectionHistory(Base):
    __tablename__ = "correction_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    field_name = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    reviewer_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="correction_history")


class ProcessingMetric(Base):
    __tablename__ = "processing_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    method = Column(String(50), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="processing_metrics")
