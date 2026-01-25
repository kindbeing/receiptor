from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Receipt
from .schemas import ReceiptCreate, ReceiptUpdate
from .database import get_db

async def get_receipts(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Receipt).offset(skip).limit(limit))
    return result.scalars().all()

async def get_receipt(db: AsyncSession, receipt_id: int):
    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    return result.scalars().first()

async def create_receipt(db: AsyncSession, receipt: ReceiptCreate):
    db_receipt = Receipt(**receipt.model_dump())
    db.add(db_receipt)
    await db.commit()
    await db.refresh(db_receipt)
    return db_receipt

async def update_receipt(db: AsyncSession, receipt_id: int, receipt_update: ReceiptUpdate):
    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    db_receipt = result.scalars().first()
    if db_receipt:
        for key, value in receipt_update.model_dump(exclude_unset=True).items():
            setattr(db_receipt, key, value)
        await db.commit()
        await db.refresh(db_receipt)
    return db_receipt

async def delete_receipt(db: AsyncSession, receipt_id: int):
    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    db_receipt = result.scalars().first()
    if db_receipt:
        await db.delete(db_receipt)
        await db.commit()
    return db_receipt
