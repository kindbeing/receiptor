from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from models import Receipt, VendorMatch, Invoice, CorrectionHistory, ExtractedField
from schemas import ReceiptCreate, ReceiptUpdate
from database import get_db

async def get_receipts(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Receipt).offset(skip).limit(limit))
    return result.scalars().all()

async def get_receipt(db: AsyncSession, receipt_id: int):
    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    return result.scalars().first()

async def create_receipt(db: AsyncSession, receipt: ReceiptCreate):
    db_receipt = Receipt(**receipt.model_dump())
    db.add(db_receipt)
    await db.commit()
    await db.refresh(db_receipt)
    return db_receipt

async def update_receipt(db: AsyncSession, receipt_id: int, receipt_update: ReceiptUpdate):
    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    db_receipt = result.scalars().first()
    if db_receipt:
        for key, value in receipt_update.model_dump(exclude_unset=True).items():
            setattr(db_receipt, key, value)
        await db.commit()
        await db.refresh(db_receipt)
    return db_receipt

async def delete_receipt(db: AsyncSession, receipt_id: int):
    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    db_receipt = result.scalars().first()
    if db_receipt:
        await db.delete(db_receipt)
        await db.commit()
    return db_receipt


# Invoice and Vendor Match CRUD operations

async def get_invoice(db: AsyncSession, invoice_id: UUID):
    """Get invoice by ID"""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    return result.scalars().first()


async def create_vendor_match(
    db: AsyncSession,
    invoice_id: UUID,
    subcontractor_id: UUID,
    match_score: int,
    confirmed: bool = False
) -> VendorMatch:
    """Create a new vendor match record"""
    vendor_match = VendorMatch(
        invoice_id=invoice_id,
        subcontractor_id=subcontractor_id,
        match_score=match_score,
        confirmed_at=datetime.utcnow() if confirmed else None
    )
    db.add(vendor_match)
    await db.commit()
    await db.refresh(vendor_match)
    return vendor_match


async def get_vendor_match(db: AsyncSession, invoice_id: UUID) -> VendorMatch:
    """Get the most recent vendor match for an invoice"""
    result = await db.execute(
        select(VendorMatch)
        .where(VendorMatch.invoice_id == invoice_id)
        .order_by(VendorMatch.created_at.desc())
    )
    return result.scalars().first()


async def update_invoice_status(db: AsyncSession, invoice_id: UUID, status: str):
    """Update invoice status"""
    invoice = await get_invoice(db, invoice_id)
    if invoice:
        invoice.status = status
        invoice.updated_at = datetime.now()
        await db.commit()
        await db.refresh(invoice)
    return invoice


async def save_correction(
    db: AsyncSession,
    invoice_id: UUID,
    field_name: str,
    original_value: str,
    corrected_value: str,
    corrected_by: str = None
) -> CorrectionHistory:
    """Create a correction history record"""
    from uuid import uuid4
    correction = CorrectionHistory(
        id=uuid4(),
        invoice_id=invoice_id,
        field_name=field_name,
        original_value=original_value,
        corrected_value=corrected_value,
        corrected_by=corrected_by,
        correction_type='manual_review',
        created_at=datetime.now()
    )
    db.add(correction)
    await db.commit()
    await db.refresh(correction)
    return correction


async def get_corrections_for_invoice(db: AsyncSession, invoice_id: UUID):
    """Get all corrections for an invoice"""
    result = await db.execute(
        select(CorrectionHistory)
        .where(CorrectionHistory.invoice_id == invoice_id)
        .order_by(CorrectionHistory.created_at.desc())
    )
    return result.scalars().all()


async def update_extracted_field(
    db: AsyncSession,
    invoice_id: UUID,
    processing_method: str,
    field_name: str,
    new_value: any
):
    """Update a specific extracted field value"""
    result = await db.execute(
        select(ExtractedField)
        .where(
            ExtractedField.invoice_id == invoice_id,
            ExtractedField.processing_method == processing_method
        )
    )
    extracted_field = result.scalars().first()
    if extracted_field:
        setattr(extracted_field, field_name, new_value)
        await db.commit()
        await db.refresh(extracted_field)
    return extracted_field
