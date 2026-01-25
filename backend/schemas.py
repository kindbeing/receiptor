from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Any
from uuid import UUID

class ReceiptBase(BaseModel):
    total: float
    vendor: str
    description: Optional[str] = None

class ReceiptCreate(ReceiptBase):
    pass

class ReceiptUpdate(BaseModel):
    total: Optional[float] = None
    vendor: Optional[str] = None
    description: Optional[str] = None

class Receipt(ReceiptBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date: datetime


# Invoice Automation Schemas

class InvoiceUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    filename: str
    file_path: str
    builder_id: UUID
    status: str
    uploaded_at: datetime
    created_at: datetime


class LineItemBase(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: float


class LineItemResponse(LineItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    amount: float
    suggested_code: Optional[str] = None
    confidence: Optional[float] = None
    confirmed_code: Optional[str] = None
    created_at: datetime


class ExtractedFieldsBase(BaseModel):
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    total_amount: Optional[float] = None


class ExtractionResult(BaseModel):
    """API contract for extraction results - used by both OCR and Vision AI"""
    invoice_id: UUID
    processing_method: str  # "traditional" or "vision"
    extraction_status: str  # "success", "partial", "failed"
    fields: ExtractedFieldsBase
    line_items: List[LineItemBase]
    confidence: float  # 0.0 to 1.0
    processing_time_ms: int
    raw_output: Optional[Any] = None
    created_at: datetime


class ExtractedFieldResponse(ExtractedFieldsBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    confidence: Optional[float] = None
    raw_json: Optional[dict] = None
    created_at: datetime


class SubcontractorBase(BaseModel):
    name: str
    builder_id: UUID
    contact_info: Optional[dict] = None


class SubcontractorResponse(SubcontractorBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime


class VendorMatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    subcontractor_id: Optional[UUID] = None
    match_score: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime


class CostCodeBase(BaseModel):
    code: str
    label: str
    description: Optional[str] = None
    builder_id: UUID


class CostCodeResponse(CostCodeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime


class ProcessingMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    method: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime


class InvoiceDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    filename: str
    file_path: str
    builder_id: UUID
    uploaded_at: datetime
    status: str
    processing_method: Optional[str] = None
    created_at: datetime
    extracted_fields: Optional[ExtractedFieldResponse] = None
    line_items: List[LineItemResponse] = []
    vendor_matches: List[VendorMatchResponse] = []
    processing_metrics: List[ProcessingMetricResponse] = []
