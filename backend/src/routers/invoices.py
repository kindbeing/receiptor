from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from datetime import datetime
from pathlib import Path

from database import get_db
from models import Invoice, ExtractedField, LineItem, ProcessingMetric
from schemas import InvoiceUploadResponse, InvoiceDetailResponse, ExtractionResult
from services.invoice_storage_service import storage_service
from services.vision_ai_service import vision_service
from services.traditional_ocr_service import TraditionalOCRService
from services.vendor_matching_service import VendorMatchingService, MatchCandidate
from services.cost_code_service import cost_code_service
from services.comparison_service import comparison_service
from services.review_workflow_service import review_workflow_service
from crud import create_vendor_match, update_invoice_status, get_invoice as crud_get_invoice

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

# Initialize services
traditional_ocr_service = TraditionalOCRService()


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
    
    # Query with relationships eagerly loaded
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.extracted_fields),
            selectinload(Invoice.line_items),
            selectinload(Invoice.vendor_matches),
            selectinload(Invoice.processing_metrics)
        )
        .where(Invoice.id == invoice_uuid)
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


@router.post("/{invoice_id}/extract/traditional", response_model=ExtractionResult)
async def extract_traditional(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract invoice data using Traditional OCR (Tesseract + regex).
    
    Args:
        invoice_id: UUID of the invoice
        db: Database session
    
    Returns:
        ExtractionResult with extracted fields, line items, and confidence scores
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    # Get invoice from database
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_uuid)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update status to processing
    invoice.status = "processing"
    await db.commit()
    
    try:
        # Process invoice with Traditional OCR
        extraction_result = traditional_ocr_service.process(
            invoice_path=invoice.file_path,
            invoice_id=str(invoice.id)
        )
        
        # Save extracted fields to database
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
        
        # Save line items
        for item in extraction_result.line_items:
            line_item = LineItem(
                invoice_id=invoice.id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.total
            )
            db.add(line_item)
        
        # Save processing metrics
        metric = ProcessingMetric(
            invoice_id=invoice.id,
            method="traditional",
            processing_time_ms=extraction_result.processing_time_ms
        )
        db.add(metric)
        
        # Update invoice status
        invoice.status = "extracted"
        invoice.processing_method = "traditional"
        
        await db.commit()
        
        return extraction_result
        
    except Exception as e:
        # Rollback to uploaded state on error
        invoice.status = "uploaded"
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Traditional OCR extraction failed: {str(e)}"
        )


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


@router.post("/{invoice_id}/match-vendor")
async def match_vendor(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Match extracted vendor name to known subcontractors using fuzzy matching.
    
    Args:
        invoice_id: UUID of the invoice
        db: Database session
    
    Returns:
        Top 3 match candidates with scores, or flag for "Add New Vendor"
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    # Get invoice
    invoice = await crud_get_invoice(db, invoice_uuid)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if invoice has been extracted
    if invoice.status not in ["extracted", "matched", "classified"]:
        raise HTTPException(
            status_code=400,
            detail="Invoice must be extracted before vendor matching"
        )
    
    # Get extracted vendor name - prioritize highest confidence extraction
    result = await db.execute(
        select(ExtractedField)
        .where(ExtractedField.invoice_id == invoice_uuid)
        .order_by(ExtractedField.confidence.desc())
    )
    extracted_field = result.scalars().first()
    
    if not extracted_field or not extracted_field.vendor_name:
        raise HTTPException(
            status_code=400,
            detail="No vendor name found in extracted data"
        )
    
    # Perform fuzzy matching
    vendor_matching_service = VendorMatchingService(db)
    matches = await vendor_matching_service.match(
        extracted_vendor=extracted_field.vendor_name,
        builder_id=invoice.builder_id,
        limit=3
    )
    
    # If we have a high-confidence match (score >= 85), save it to database
    if matches and matches[0].score >= 85:
        top_match = matches[0]
        await create_vendor_match(
            db=db,
            invoice_id=invoice.id,
            subcontractor_id=top_match.subcontractor_id,
            match_score=top_match.score,
            confirmed=False  # Will be confirmed by user or automatically
        )
        
        # Update invoice status to 'matched' or 'needs_review'
        if top_match.score >= 90:
            await update_invoice_status(db, invoice.id, "matched")
            status = "matched"
        else:
            await update_invoice_status(db, invoice.id, "needs_review")
            status = "needs_review"
    else:
        # Low confidence or no matches - needs review
        await update_invoice_status(db, invoice.id, "needs_review")
        status = "needs_review"
    
    # Return match results
    return {
        "invoice_id": str(invoice.id),
        "extracted_vendor": extracted_field.vendor_name,
        "matches": [
            {
                "subcontractor_id": str(m.subcontractor_id),
                "subcontractor_name": m.subcontractor_name,
                "score": m.score,
                "confidence_level": vendor_matching_service.get_confidence_level(m.score),
                "contact_info": m.contact_info
            }
            for m in matches
        ],
        "status": status,
        "message": "High confidence match" if status == "matched" else "Review required"
    }


@router.post("/{invoice_id}/classify-costs")
async def classify_costs(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Classify invoice line items to cost codes using semantic similarity.
    
    Args:
        invoice_id: UUID of the invoice
        db: Database session
    
    Returns:
        Classification results with suggested codes and confidence scores
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    # Get invoice
    invoice = await crud_get_invoice(db, invoice_uuid)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if invoice has been extracted
    if invoice.status not in ["extracted", "matched", "classified", "needs_review"]:
        raise HTTPException(
            status_code=400,
            detail="Invoice must be extracted before cost code classification"
        )
    
    # Get line items
    result = await db.execute(
        select(LineItem).where(LineItem.invoice_id == invoice_uuid)
    )
    line_items = result.scalars().all()
    
    if not line_items:
        raise HTTPException(
            status_code=400,
            detail="No line items found for this invoice"
        )
    
    # Convert to dict format for service
    line_items_dict = [
        {
            "id": str(item.id),
            "description": item.description,
            "quantity": float(item.quantity) if item.quantity else None,
            "unit_price": float(item.unit_price) if item.unit_price else None,
            "amount": float(item.amount)
        }
        for item in line_items
    ]
    
    # Classify using cost code service
    classified_items = await cost_code_service.classify_line_items(
        line_items=line_items_dict,
        builder_id=str(invoice.builder_id),
        db=db
    )
    
    # Update line items in database with suggested codes
    needs_review = False
    for classified in classified_items:
        item_id = uuid.UUID(classified['id'])
        result = await db.execute(
            select(LineItem).where(LineItem.id == item_id)
        )
        line_item = result.scalar_one_or_none()
        
        if line_item:
            line_item.suggested_code = classified.get('suggested_code')
            line_item.confidence = classified.get('confidence')
            
            # Flag for review if confidence < 60%
            if classified.get('confidence', 0) < 0.60:
                needs_review = True
    
    # Update invoice status
    if needs_review and invoice.status != "needs_review":
        await update_invoice_status(db, invoice.id, "needs_review")
        status = "needs_review"
    else:
        await update_invoice_status(db, invoice.id, "classified")
        status = "classified"
    
    await db.commit()
    
    # Return classification results
    return {
        "invoice_id": str(invoice.id),
        "line_items": classified_items,
        "status": status,
        "needs_review": needs_review,
        "message": "Classification complete" if not needs_review else "Review required for low-confidence items"
    }


@router.get("/{invoice_id}/comparison")
async def get_comparison(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get side-by-side comparison of Traditional OCR vs Vision AI extraction results.
    
    Args:
        invoice_id: UUID of the invoice
        db: Database session
    
    Returns:
        Comparison data with both methods' results and metrics
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    try:
        comparison_data = await comparison_service.compare(invoice_uuid, db)
        return comparison_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.patch("/{invoice_id}/status")
async def update_status(
    invoice_id: str,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Update invoice status (approve/reject/needs_review).
    
    Args:
        invoice_id: UUID of the invoice
        status: New status (approved, rejected, needs_review)
        db: Database session
    
    Returns:
        Updated invoice data
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    try:
        updated_invoice = await review_workflow_service.update_invoice_status(
            invoice_id=invoice_uuid,
            new_status=status,
            db=db
        )
        
        return {
            "invoice_id": str(updated_invoice.id),
            "status": updated_invoice.status,
            "updated_at": updated_invoice.updated_at.isoformat(),
            "message": f"Invoice status updated to '{status}'"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@router.post("/{invoice_id}/corrections")
async def save_corrections(
    invoice_id: str,
    corrections: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Save human corrections to extracted fields.
    
    Args:
        invoice_id: UUID of the invoice
        corrections: Dict of field_name -> corrected_value
        db: Database session
    
    Returns:
        List of correction records created
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    try:
        correction_records = await review_workflow_service.save_corrections(
            invoice_id=invoice_uuid,
            corrections=corrections,
            db=db
        )
        
        return {
            "invoice_id": str(invoice_uuid),
            "corrections_saved": len(correction_records),
            "corrections": [
                {
                    "field_name": c.field_name,
                    "original_value": c.original_value,
                    "corrected_value": c.corrected_value,
                    "created_at": c.created_at.isoformat()
                }
                for c in correction_records
            ],
            "message": f"Saved {len(correction_records)} correction(s)"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save corrections: {str(e)}")


@router.get("/{invoice_id}/corrections")
async def get_corrections(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get correction history for an invoice.
    
    Args:
        invoice_id: UUID of the invoice
        db: Database session
    
    Returns:
        List of correction records
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    try:
        corrections = await review_workflow_service.get_corrections_for_invoice(
            invoice_id=invoice_uuid,
            db=db
        )
        
        return {
            "invoice_id": str(invoice_uuid),
            "corrections": [
                {
                    "id": str(c.id),
                    "field_name": c.field_name,
                    "original_value": c.original_value,
                    "corrected_value": c.corrected_value,
                    "corrected_by": c.corrected_by,
                    "correction_type": c.correction_type,
                    "created_at": c.created_at.isoformat()
                }
                for c in corrections
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get corrections: {str(e)}")


@router.get("/{invoice_id}/image")
async def get_invoice_image(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the original invoice image/PDF file.
    
    Args:
        invoice_id: UUID of the invoice
        db: Database session
    
    Returns:
        FileResponse with the invoice image
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invoice_id format")
    
    # Get invoice from database
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_uuid)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get the file path from storage service
    try:
        file_path = storage_service.get_original_file_path(invoice.id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Invoice image file not found")
    
    # Determine media type based on file extension
    ext = file_path.suffix.lower()
    media_type_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.pdf': 'application/pdf'
    }
    media_type = media_type_map.get(ext, 'application/octet-stream')
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=invoice.filename
    )
