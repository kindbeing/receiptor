from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Invoice, ExtractedField, CorrectionHistory
from datetime import datetime
import uuid
from typing import Dict, Optional, List


class ReviewWorkflowService:
    """
    Service for managing human review workflow:
    - Status updates (approved/rejected)
    - Human corrections tracking
    - Audit trail management
    """
    
    async def update_invoice_status(
        self,
        invoice_id: uuid.UUID,
        new_status: str,
        db: AsyncSession,
        user_id: Optional[str] = None
    ) -> Invoice:
        """
        Update invoice status (approve/reject).
        
        Args:
            invoice_id: UUID of the invoice
            new_status: One of: approved, rejected, needs_review
            db: Database session
            user_id: Optional user ID for audit trail
            
        Returns:
            Updated Invoice object
        """
        # Validate status
        valid_statuses = ['approved', 'rejected', 'needs_review']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")
        
        # Get invoice
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError("Invoice not found")
        
        # Update status
        invoice.status = new_status
        invoice.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(invoice)
        
        return invoice
    
    async def save_corrections(
        self,
        invoice_id: uuid.UUID,
        corrections: Dict[str, any],
        db: AsyncSession,
        user_id: Optional[str] = None
    ) -> List[CorrectionHistory]:
        """
        Save human corrections and update extracted fields.
        
        Args:
            invoice_id: UUID of the invoice
            corrections: Dict of field_name -> corrected_value
            db: Database session
            user_id: Optional user ID for audit trail
            
        Returns:
            List of CorrectionHistory records created
        """
        # Get invoice
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError("Invoice not found")
        
        # Get existing extracted fields
        result = await db.execute(
            select(ExtractedField).where(
                ExtractedField.invoice_id == invoice_id
            )
        )
        extracted_fields = result.scalars().all()
        
        # Group by processing method
        fields_by_method = {}
        for ef in extracted_fields:
            fields_by_method[ef.processing_method] = ef
        
        correction_records = []
        
        # Process each correction
        for field_name, new_value in corrections.items():
            # Determine which processing method to use (prefer vision, fallback to traditional)
            processing_method = None
            original_value = None
            
            if 'vision' in fields_by_method:
                processing_method = 'vision'
                original_value = getattr(fields_by_method['vision'], field_name, None)
            elif 'traditional' in fields_by_method:
                processing_method = 'traditional'
                original_value = getattr(fields_by_method['traditional'], field_name, None)
            
            if processing_method is None:
                continue  # No extracted fields to correct
            
            # Skip if value hasn't changed
            if original_value == new_value:
                continue
            
            # Create correction history record
            correction = CorrectionHistory(
                id=uuid.uuid4(),
                invoice_id=invoice_id,
                field_name=field_name,
                original_value=str(original_value) if original_value is not None else None,
                corrected_value=str(new_value) if new_value is not None else None,
                corrected_by=user_id,
                correction_type='manual_review',
                created_at=datetime.now()
            )
            db.add(correction)
            correction_records.append(correction)
            
            # Update the extracted field with corrected value
            extracted_field = fields_by_method[processing_method]
            setattr(extracted_field, field_name, new_value)
        
        # Commit all changes
        await db.commit()
        
        # Refresh correction records
        for correction in correction_records:
            await db.refresh(correction)
        
        return correction_records
    
    async def get_corrections_for_invoice(
        self,
        invoice_id: uuid.UUID,
        db: AsyncSession
    ) -> List[CorrectionHistory]:
        """
        Get all corrections made to an invoice.
        
        Args:
            invoice_id: UUID of the invoice
            db: Database session
            
        Returns:
            List of CorrectionHistory records
        """
        result = await db.execute(
            select(CorrectionHistory)
            .where(CorrectionHistory.invoice_id == invoice_id)
            .order_by(CorrectionHistory.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_invoices_by_status(
        self,
        builder_id: uuid.UUID,
        status: Optional[str],
        db: AsyncSession,
        limit: int = 100
    ) -> List[Invoice]:
        """
        Get invoices filtered by status.
        
        Args:
            builder_id: UUID of the builder
            status: Optional status filter (needs_review, approved, rejected, etc.)
            db: Database session
            limit: Maximum number of invoices to return
            
        Returns:
            List of Invoice objects
        """
        query = select(Invoice).where(Invoice.builder_id == builder_id)
        
        if status:
            query = query.where(Invoice.status == status)
        
        query = query.order_by(Invoice.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()


# Singleton instance
review_workflow_service = ReviewWorkflowService()

