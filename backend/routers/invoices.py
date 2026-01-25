from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
from datetime import datetime

from database import get_db
from models import Invoice, ExtractedField, LineItem, ProcessingMetric
from schemas import InvoiceUploadResponse, InvoiceDetailResponse, ExtractionResult
from services.invoice_storage_service import storage_service
from services.vision_ai_service import vision_service

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.post("/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    builder_id: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an invoice file (PDF, JPG, PNG).
    
    Args:
        file: The invoice file to upload
        builder_id: UUID of the builder/contractor
        db: Database session
    
    Returns:
        InvoiceUploadResponse with invoice_id and metadata
    """
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: PDF, JPG, PNG. Got: {file.content_type}"
        )
    
    # Validate builder_id is valid UUID
    try:
        builder_uuid = uuid.UUID(builder_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid builder_id format")
    
    # Create invoice record
    invoice = Invoice(
        filename=file.filename or "unknown.pdf",
        file_path="",  # Will update after saving file
        builder_id=builder_uuid,
        status="uploaded"
    )
    
    db.add(invoice)
    await db.flush()  # Get the invoice.id before saving file
    
    # Save file to disk
    try:
        file_path = await storage_service.save_invoice(file, invoice.id)
        invoice.file_path = file_path
        await db.commit()
        await db.refresh(invoice)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get invoice details by ID.
    
    Args:
        invoice_id: UUID of the invoice
        db: Database session
    
    Returns:
        InvoiceDetailResponse with all related data
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    # Query with relationships
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_uuid)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice


@router.get("/", response_model=List[InvoiceUploadResponse])
async def list_invoices(
    builder_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List invoices with optional filters.
    
    Args:
        builder_id: Filter by builder UUID
        status: Filter by invoice status
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of InvoiceUploadResponse
    """
    query = select(Invoice)
    
    # Apply filters
    if builder_id:
        try:
            builder_uuid = uuid.UUID(builder_id)
            query = query.where(Invoice.builder_id == builder_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid builder_id format")
    
    if status:
        query = query.where(Invoice.status == status)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Invoice.uploaded_at.desc())
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    return invoices


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an invoice and its associated files.
    
    Args:
        invoice_id: UUID of the invoice
        db: Database session
    
    Returns:
        Success message
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_uuid)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete files from disk
    try:
        storage_service.delete_invoice_files(invoice.id)
    except Exception as e:
        # Log error but continue with DB deletion
        print(f"Warning: Failed to delete files for invoice {invoice_id}: {e}")
    
    # Delete from database (cascade will delete related records)
    await db.delete(invoice)
    await db.commit()
    
    return {"detail": "Invoice deleted successfully"}


@router.post("/{invoice_id}/extract/vision", response_model=ExtractionResult)
async def extract_vision(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_uuid)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.status = "processing"
    await db.commit()
    
    try:
        extraction_result = vision_service.process(invoice.file_path)
        extraction_result.invoice_id = invoice.id
        
        extracted_field = ExtractedField(
            invoice_id=invoice.id,
            vendor_name=extraction_result.fields.vendor_name,
            invoice_number=extraction_result.fields.invoice_number,
            invoice_date=extraction_result.fields.invoice_date,
            total_amount=extraction_result.fields.total_amount,
            confidence=extraction_result.confidence,
            raw_json=extraction_result.raw_output
        )
        db.add(extracted_field)
        
        for item in extraction_result.line_items:
            line_item = LineItem(
                invoice_id=invoice.id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.total
            )
            db.add(line_item)
        
        metric = ProcessingMetric(
            invoice_id=invoice.id,
            method="vision",
            processing_time_ms=extraction_result.processing_time_ms
        )
        db.add(metric)
        
        invoice.status = "extracted"
        invoice.processing_method = "vision"
        
        await db.commit()
        
        return extraction_result
        
    except Exception as e:
        invoice.status = "uploaded"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Vision extraction failed: {str(e)}")

