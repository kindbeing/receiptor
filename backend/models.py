from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.sql import func
from database import Base

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=func.now())
    total = Column(Float, nullable=False)
    vendor = Column(String, index=True)
    description = Column(Text)
