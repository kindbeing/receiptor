from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

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
