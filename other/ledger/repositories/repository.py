from __future__ import annotations

from typing import Optional, Tuple, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.repository import BaseRepository
from app.domains.ledger.models.model import LedgerEntry, StockLedger


class LedgerEntryRepository(BaseRepository):
    async def get_by_id(self, entry_id: str) -> LedgerEntry | None:
        return await self.db.get(LedgerEntry, entry_id)

    async def list(
        self,
        *,
        product_id: str | None = None,
        batch_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[LedgerEntry], int]:
        stmt = select(LedgerEntry).order_by(LedgerEntry.created_at.desc())
        count_stmt = select(func.count()).select_from(LedgerEntry)
        if product_id:
            stmt = stmt.where(LedgerEntry.product_id == product_id)
            count_stmt = count_stmt.where(LedgerEntry.product_id == product_id)
        if batch_id:
            stmt = stmt.where(LedgerEntry.batch_id == batch_id)
            count_stmt = count_stmt.where(LedgerEntry.batch_id == batch_id)

        rows = (await self.db.execute(stmt.limit(limit).offset(offset))).scalars().all()
        total = (await self.db.execute(count_stmt)).scalar_one()
        return list(rows), int(total)

    async def create(self, data: dict) -> LedgerEntry:
        entry = LedgerEntry(**data)
        return await self.add_and_refresh(entry)


class StockLedgerRepository(BaseRepository):
    async def get_by_id(self, row_id: str) -> StockLedger | None:
        return await self.db.get(StockLedger, row_id)

    async def list(
        self,
        *,
        product_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[StockLedger], int]:
        stmt = select(StockLedger).order_by(StockLedger.created_at.desc())
        count_stmt = select(func.count()).select_from(StockLedger)
        if product_id:
            stmt = stmt.where(StockLedger.product_id == product_id)
            count_stmt = count_stmt.where(StockLedger.product_id == product_id)
        if batch_id:
            stmt = stmt.where(StockLedger.batch_id == batch_id)
            count_stmt = count_stmt.where(StockLedger.batch_id == batch_id)

        rows = (await self.db.execute(stmt.limit(limit).offset(offset))).scalars().all()
        total = (await self.db.execute(count_stmt)).scalar_one()
        return list(rows), int(total)

    async def create(self, data: dict) -> StockLedger:
        row = StockLedger(**data)
        return await self.add_and_refresh(row)


__all__ = ["LedgerEntryRepository", "StockLedgerRepository"]
