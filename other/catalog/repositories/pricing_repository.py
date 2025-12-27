from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domains.catalog.models.pricing import PriceList


class PriceListRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, *, limit: int, offset: int, active_only: bool = False) -> Tuple[List[PriceList], int]:
        stmt = select(PriceList).order_by(PriceList.created_at.desc())
        if active_only:
            stmt = stmt.where(PriceList.is_active == True)  # noqa: E712
        total_stmt = select(func.count()).select_from(stmt.subquery())
        rows = (await self.db.execute(stmt.limit(limit).offset(offset))).scalars().all()
        total = (await self.db.execute(total_stmt)).scalar_one()
        return list(rows), int(total or 0)

    async def list_active_for_date(self, *, target_date, currency: str | None = None) -> list[PriceList]:
        stmt = select(PriceList).where(PriceList.is_active == True)  # noqa: E712
        if currency:
            stmt = stmt.where(PriceList.currency == currency)
        if target_date is not None:
            stmt = stmt.where(
                (PriceList.valid_from.is_(None) | (PriceList.valid_from <= target_date))
                & (PriceList.valid_to.is_(None) | (PriceList.valid_to >= target_date))
            )
        return list((await self.db.execute(stmt.order_by(PriceList.created_at.desc()))).scalars().all())

    async def get(self, price_list_id: str) -> Optional[PriceList]:
        return await self.db.get(PriceList, price_list_id)

    async def create(self, data: dict) -> PriceList:
        row = PriceList(**data)
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def update(self, price_list_id: str, data: dict) -> PriceList:
        row = await self.get(price_list_id)
        if not row:
            raise DomainError("Price list not found", status_code=404, code="price_list_not_found")
        for key, value in data.items():
            setattr(row, key, value)
        await self.db.flush()
        await self.db.refresh(row)
        return row


__all__ = ["PriceListRepository"]
