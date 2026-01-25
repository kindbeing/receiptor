from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..crud import get_receipts, get_receipt, create_receipt, update_receipt, delete_receipt
from ..schemas import Receipt, ReceiptCreate, ReceiptUpdate

router = APIRouter(prefix="/receipts", tags=["receipts"])

@router.get("/", response_model=List[Receipt])
async def read_receipts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    receipts = await get_receipts(db, skip=skip, limit=limit)
    return receipts

@router.get("/{receipt_id}", response_model=Receipt)
async def read_receipt(receipt_id: int, db: AsyncSession = Depends(get_db)):
    db_receipt = await get_receipt(db, receipt_id=receipt_id)
    if db_receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return db_receipt

@router.post("/", response_model=Receipt)
async def create_receipt_endpoint(receipt: ReceiptCreate, db: AsyncSession = Depends(get_db)):
    return await create_receipt(db=db, receipt=receipt)

@router.put("/{receipt_id}", response_model=Receipt)
async def update_receipt_endpoint(receipt_id: int, receipt: ReceiptUpdate, db: AsyncSession = Depends(get_db)):
    db_receipt = await update_receipt(db, receipt_id, receipt)
    if db_receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return db_receipt

@router.delete("/{receipt_id}")
async def delete_receipt_endpoint(receipt_id: int, db: AsyncSession = Depends(get_db)):
    db_receipt = await delete_receipt(db, receipt_id)
    if db_receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return {"detail": "Receipt deleted"}
