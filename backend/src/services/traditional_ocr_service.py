"""
Traditional OCR Extraction Service
Uses Tesseract OCR + regex parsing to extract structured data from invoices.
"""
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

from schemas import ExtractedFieldsBase, LineItemBase, ExtractionResult


class TraditionalOCRService:
    """
    Traditional OCR extraction pipeline:
    1. Convert PDF to images (if needed)
    2. Run Tesseract OCR
    3. Parse text with regex patterns
    4. Extract fields and line items
    """
    
    def __init__(self):
        # Regex patterns for field extraction
        self.patterns = {
            'total': [
                r'(?i)(?:total|amount\s+due|balance\s+due)[\s:$]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'(?i)(?:grand\s+total|invoice\s+total)[\s:$]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})\s*(?:total|due)',
            ],
            'invoice_number': [
                r'(?i)invoice\s*(?:#|no|number)[\s:]*([A-Z0-9-]+)',
                r'(?i)inv[\s#:]+([A-Z0-9-]+)',
                r'#\s*([A-Z0-9-]{3,})',
            ],
            'date': [
                # YYYY-MM-DD format
                r'(?i)(?:invoice\s+)?date[\s:]*(\d{4}-\d{1,2}-\d{1,2})',
                # MM/DD/YYYY or MM-DD-YYYY
                r'(?i)(?:invoice\s+)?date[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?i)date[\s:]*(\d{1,2}/\d{1,2}/\d{2,4})',
                # Any YYYY-MM-DD standalone
                r'(\d{4}-\d{1,2}-\d{1,2})',
                # Any MM/DD/YYYY standalone
                r'(\d{1,2}/\d{1,2}/\d{4})',
            ],
            'vendor': [
                r'^([A-Z][A-Za-z\s&,.]+(?:LLC|Inc|Corp|Co|Company|Ltd|Limited))',
                r'^([A-Z][A-Za-z\s&,.]+)',
            ]
        }
    
    def process(self, invoice_path: str, invoice_id: str) -> ExtractionResult:
        """
        Process an invoice and extract structured data.
        
        Args:
            invoice_path: Path to the invoice file (PDF or image)
            invoice_id: UUID of the invoice
            
        Returns:
            ExtractionResult with extracted fields and metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Get text from document
            ocr_text = self._extract_text(invoice_path)
            
            # Step 2: Extract structured fields
            fields = self._parse_fields(ocr_text)
            
            # Step 3: Extract line items
            line_items = self._parse_line_items(ocr_text)
            
            # Step 4: Calculate confidence
            confidence = self._calculate_confidence(fields, line_items)
            
            # Determine extraction status
            status = "success" if confidence > 0.7 else "partial" if confidence > 0.3 else "failed"
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return ExtractionResult(
                invoice_id=invoice_id,
                processing_method="traditional",
                extraction_status=status,
                fields=ExtractedFieldsBase(**fields),
                line_items=[LineItemBase(**item) for item in line_items],
                confidence=confidence,
                processing_time_ms=processing_time,
                raw_output={"ocr_text": ocr_text[:500]},  # First 500 chars for debugging
                created_at=datetime.now()
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            return ExtractionResult(
                invoice_id=invoice_id,
                processing_method="traditional",
                extraction_status="failed",
                fields=ExtractedFieldsBase(),
                line_items=[],
                confidence=0.0,
                processing_time_ms=processing_time,
                raw_output={"error": str(e)},
                created_at=datetime.now()
            )
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF or image using Tesseract OCR."""
        path = Path(file_path)
        
        if path.suffix.lower() == '.pdf':
            # Convert PDF to images
            images = convert_from_path(file_path, dpi=300, first_page=1, last_page=1)
            # OCR the first page
            text = pytesseract.image_to_string(images[0], config='--psm 6')
        else:
            # Direct image OCR
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, config='--psm 6')
        
        return text
    
    def _parse_fields(self, text: str) -> Dict[str, Any]:
        """Parse structured fields from OCR text using regex patterns."""
        fields = {
            'vendor_name': None,
            'invoice_number': None,
            'invoice_date': None,
            'total_amount': None
        }
        
        # Extract vendor (usually in first few lines)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Try first 3 lines for vendor name
            for line in lines[:3]:
                for pattern in self.patterns['vendor']:
                    match = re.search(pattern, line)
                    if match:
                        fields['vendor_name'] = match.group(1).strip()
                        break
                if fields['vendor_name']:
                    break
        
        # Extract invoice number
        for pattern in self.patterns['invoice_number']:
            match = re.search(pattern, text)
            if match:
                fields['invoice_number'] = match.group(1).strip()
                break
        
        # Extract date
        for pattern in self.patterns['date']:
            match = re.search(pattern, text)
            if match:
                fields['invoice_date'] = match.group(1).strip()
                break
        
        # Extract total amount
        for pattern in self.patterns['total']:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    fields['total_amount'] = float(amount_str)
                except ValueError:
                    continue
                break
        
        return fields
    
    def _parse_line_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse line items from OCR text.
        This is a basic implementation - looks for patterns like:
        Description  Qty  Price  Amount
        """
        line_items = []
        
        # Pattern 1: description followed by numbers (quantity, price, total)
        # Example: "Plumbing work  10  50.00  500.00"
        pattern = r'([A-Za-z][A-Za-z\s-]+)\s+(\d+(?:\.\d{2})?)\s+(?:\$)?(\d+\.\d{2})\s+(?:\$)?(\d+\.\d{2})'
        
        for match in re.finditer(pattern, text):
            description = match.group(1).strip()
            quantity = float(match.group(2))
            unit_price = float(match.group(3))
            total = float(match.group(4))
            
            line_items.append({
                'description': description,
                'quantity': quantity,
                'unit_price': unit_price,
                'total': total
            })
        
        # Pattern 2: More flexible - description with amount (handles dashes, special chars)
        # Example: "Install copper piping – rough-in $3,200.00"
        if not line_items:
            # Match descriptions with amounts, including em-dashes, hyphens, etc.
            flexible_pattern = r'([A-Za-z][A-Za-z\s\-–—,]+)\s+\$?([\d,]+\.\d{2})'
            
            for match in re.finditer(flexible_pattern, text):
                description = match.group(1).strip()
                amount_str = match.group(2).replace(',', '')
                
                # Filter out header-like text and ensure reasonable description length
                if len(description) > 10 and not re.search(r'(?i)(invoice|total|subtotal|tax|balance|due)', description):
                    try:
                        total = float(amount_str)
                        # Only add if amount is reasonable (> $10, < $1,000,000)
                        if 10.0 <= total <= 1000000.0:
                            line_items.append({
                                'description': description,
                                'quantity': None,
                                'unit_price': None,
                                'total': total
                            })
                    except ValueError:
                        continue
        
        # Pattern 3: Fallback - simple description and amount without special formatting
        if not line_items:
            # Just description and amount
            simple_pattern = r'([A-Za-z][A-Za-z\s-]{10,})\s+(?:\$)?(\d+\.\d{2})'
            for match in re.finditer(simple_pattern, text):
                description = match.group(1).strip()
                total = float(match.group(2))
                
                line_items.append({
                    'description': description,
                    'quantity': None,
                    'unit_price': None,
                    'total': total
                })
        
        return line_items
    
    def _calculate_confidence(self, fields: Dict[str, Any], line_items: List[Dict[str, Any]]) -> float:
        """
        Calculate overall extraction confidence based on what was extracted.
        
        Scoring:
        - Vendor name: 25%
        - Invoice number: 15%
        - Date: 15%
        - Total amount: 25%
        - Line items: 20%
        """
        score = 0.0
        
        if fields.get('vendor_name'):
            score += 0.25
        if fields.get('invoice_number'):
            score += 0.15
        if fields.get('invoice_date'):
            score += 0.15
        if fields.get('total_amount') is not None:
            score += 0.25
        if line_items:
            score += 0.20
        
        return round(score, 2)

