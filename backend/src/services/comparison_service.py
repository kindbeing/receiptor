from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Invoice, ExtractedField, LineItem, ProcessingMetric
from typing import Dict, List, Optional, Any
import uuid


class ComparisonService:
    async def compare(self, invoice_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
        """
        Compare Traditional OCR and Vision AI extraction results for an invoice.
        
        Args:
            invoice_id: UUID of the invoice
            db: Database session
            
        Returns:
            Dictionary with side-by-side comparison data
        """
        # Get invoice
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError("Invoice not found")
        
        # Get all extracted fields (both methods)
        result = await db.execute(
            select(ExtractedField).where(ExtractedField.invoice_id == invoice_id)
        )
        extracted_fields = result.scalars().all()
        
        # Get all line items
        result = await db.execute(
            select(LineItem).where(LineItem.invoice_id == invoice_id)
        )
        line_items = result.scalars().all()
        
        # Get all processing metrics
        result = await db.execute(
            select(ProcessingMetric).where(ProcessingMetric.invoice_id == invoice_id)
        )
        metrics = result.scalars().all()
        
        # Organize by method
        traditional_data = self._extract_method_data(
            extracted_fields, line_items, metrics, "traditional"
        )
        vision_data = self._extract_method_data(
            extracted_fields, line_items, metrics, "vision"
        )
        
        # Calculate comparison metrics
        comparison_metrics = self._calculate_comparison_metrics(
            traditional_data, vision_data
        )
        
        return {
            "invoice_id": str(invoice_id),
            "invoice_filename": invoice.filename,
            "traditional": traditional_data,
            "vision": vision_data,
            "comparison": comparison_metrics
        }
    
    def _extract_method_data(
        self,
        extracted_fields: List[ExtractedField],
        line_items: List[LineItem],
        metrics: List[ProcessingMetric],
        method: str
    ) -> Dict[str, Any]:
        """Extract data for a specific processing method."""
        # Find extracted field for this method (based on raw_json metadata)
        method_field = None
        for field in extracted_fields:
            if field.raw_json and isinstance(field.raw_json, dict):
                if field.raw_json.get('processing_method') == method:
                    method_field = field
                    break
        
        # Find metric for this method
        method_metric = None
        for metric in metrics:
            if metric.method == method:
                method_metric = metric
                break
        
        if not method_field:
            return {
                "available": False,
                "fields": None,
                "line_items": [],
                "confidence": None,
                "processing_time_ms": None
            }
        
        # Get line items (they're shared, so we return all for now)
        # In a real system, you'd store method-specific line items
        line_items_data = [
            {
                "description": item.description,
                "quantity": float(item.quantity) if item.quantity else None,
                "unit_price": float(item.unit_price) if item.unit_price else None,
                "amount": float(item.amount)
            }
            for item in line_items
        ]
        
        return {
            "available": True,
            "fields": {
                "vendor_name": method_field.vendor_name,
                "invoice_number": method_field.invoice_number,
                "invoice_date": method_field.invoice_date.isoformat() if method_field.invoice_date else None,
                "total_amount": float(method_field.total_amount) if method_field.total_amount else None
            },
            "line_items": line_items_data,
            "confidence": float(method_field.confidence) if method_field.confidence else None,
            "processing_time_ms": method_metric.processing_time_ms if method_metric else None
        }
    
    def _calculate_comparison_metrics(
        self,
        traditional_data: Dict[str, Any],
        vision_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comparison metrics between the two methods."""
        if not traditional_data["available"] or not vision_data["available"]:
            return {
                "field_match_rate": None,
                "time_difference_ms": None,
                "confidence_difference": None,
                "winner": None
            }
        
        # Calculate field match rate
        trad_fields = traditional_data["fields"]
        vision_fields = vision_data["fields"]
        
        matches = 0
        total_fields = 0
        
        for field_name in ["vendor_name", "invoice_number", "invoice_date", "total_amount"]:
            trad_val = trad_fields.get(field_name)
            vision_val = vision_fields.get(field_name)
            
            if trad_val is not None or vision_val is not None:
                total_fields += 1
                if trad_val == vision_val:
                    matches += 1
        
        field_match_rate = matches / total_fields if total_fields > 0 else 0
        
        # Calculate time difference
        trad_time = traditional_data.get("processing_time_ms")
        vision_time = vision_data.get("processing_time_ms")
        time_difference = None
        if trad_time is not None and vision_time is not None:
            time_difference = vision_time - trad_time
        
        # Calculate confidence difference
        trad_conf = traditional_data.get("confidence")
        vision_conf = vision_data.get("confidence")
        confidence_difference = None
        if trad_conf is not None and vision_conf is not None:
            confidence_difference = vision_conf - trad_conf
        
        # Determine winner (simple heuristic)
        winner = None
        if trad_conf is not None and vision_conf is not None:
            if vision_conf > trad_conf + 0.05:
                winner = "vision"
            elif trad_conf > vision_conf + 0.05:
                winner = "traditional"
            else:
                winner = "tie"
        
        return {
            "field_match_rate": field_match_rate,
            "time_difference_ms": time_difference,
            "confidence_difference": confidence_difference,
            "winner": winner
        }


comparison_service = ComparisonService()
