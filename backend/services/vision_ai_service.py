import ollama
import json
import time
from datetime import datetime
from typing import Optional
from pathlib import Path
from schemas import ExtractionResult, ExtractedFieldsBase, LineItemBase


class VisionAIService:
    def __init__(self, model: str = "qwen2-vl:7b"):
        self.model = model
        
    def process(self, invoice_path: str) -> ExtractionResult:
        start_time = time.time()
        
        prompt = """Analyze this invoice image and extract the following information in JSON format:

{
  "vendor_name": "exact vendor/company name",
  "invoice_number": "invoice number",
  "invoice_date": "YYYY-MM-DD format",
  "total_amount": numeric value only,
  "line_items": [
    {
      "description": "item description",
      "quantity": numeric or null,
      "unit_price": numeric or null,
      "total": numeric value
    }
  ],
  "confidence": 0.0 to 1.0
}

Return ONLY valid JSON, no additional text."""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [invoice_path]
                }]
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            raw_content = response['message']['content']
            
            json_str = self._extract_json(raw_content)
            parsed_data = json.loads(json_str)
            
            fields = ExtractedFieldsBase(
                vendor_name=parsed_data.get('vendor_name'),
                invoice_number=parsed_data.get('invoice_number'),
                invoice_date=parsed_data.get('invoice_date'),
                total_amount=parsed_data.get('total_amount')
            )
            
            line_items = [
                LineItemBase(
                    description=item['description'],
                    quantity=item.get('quantity'),
                    unit_price=item.get('unit_price'),
                    total=item['total']
                )
                for item in parsed_data.get('line_items', [])
            ]
            
            confidence = parsed_data.get('confidence', 0.85)
            extraction_status = "success" if confidence > 0.7 else "partial"
            
            return ExtractionResult(
                invoice_id=None,
                processing_method="vision",
                extraction_status=extraction_status,
                fields=fields,
                line_items=line_items,
                confidence=confidence,
                processing_time_ms=processing_time_ms,
                raw_output=parsed_data,
                created_at=datetime.utcnow()
            )
            
        except json.JSONDecodeError as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            return ExtractionResult(
                invoice_id=None,
                processing_method="vision",
                extraction_status="failed",
                fields=ExtractedFieldsBase(),
                line_items=[],
                confidence=0.0,
                processing_time_ms=processing_time_ms,
                raw_output={"error": f"JSON parsing failed: {str(e)}", "raw": raw_content},
                created_at=datetime.utcnow()
            )
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            return ExtractionResult(
                invoice_id=None,
                processing_method="vision",
                extraction_status="failed",
                fields=ExtractedFieldsBase(),
                line_items=[],
                confidence=0.0,
                processing_time_ms=processing_time_ms,
                raw_output={"error": str(e)},
                created_at=datetime.utcnow()
            )
    
    def _extract_json(self, text: str) -> str:
        text = text.strip()
        
        if text.startswith('```'):
            lines = text.split('\n')
            lines = lines[1:-1] if len(lines) > 2 else lines[1:]
            text = '\n'.join(lines)
        
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1:
            return text[start:end+1]
        
        return text


vision_service = VisionAIService()
