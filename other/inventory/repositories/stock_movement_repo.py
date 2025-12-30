from __future__ import annotations

from typing import Optional, Tuple, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.inventory.models.stock_movement import StockMovement
from app.core.db.repository import BaseRepository


class StockMovementRepository(BaseRepository):
    async def list(
        self,
        *,
        product_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[StockMovement], int]:
        stmt = select(StockMovement).order_by(StockMovement.created_at.desc())

        if product_id:
            stmt = stmt.where(StockMovement.product_id == product_id)

        total_stmt = select(func.count()).select_from(stmt.subquery())

        rows = (await self.db.execute(stmt.limit(limit).offset(offset))).scalars().all()
        total = (await self.db.execute(total_stmt)).scalar_one()

        return list(rows), int(total)

    async def create(self, data: dict) -> StockMovement:
        row = StockMovement(**data)
        return await self.add_and_refresh(row)


__all__ = ["StockMovementRepository"]
