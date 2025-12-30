from __future__ import annotations

from typing import Optional, Tuple, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.inventory.models.stock_batch import Batch
from app.core.db.repository import BaseRepository


class BatchRepository(BaseRepository):
    async def list(
        self,
        *,
        product_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Batch], int]:
        stmt = select(Batch).order_by(Batch.created_at.desc())
        count_stmt = select(func.count()).select_from(Batch)

        if product_id:
            stmt = stmt.where(Batch.product_id == product_id)
            count_stmt = count_stmt.where(Batch.product_id == product_id)

        result = await self.db.execute(stmt.limit(limit).offset(offset))
        rows = list(result.scalars().all())
        total = await self.db.scalar(count_stmt)
        return rows, int(total or 0)

    async def get(self, batch_id: str) -> Batch | None:
        stmt = select(Batch).where(Batch.id == batch_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_by_product(self, product_id: str) -> list[Batch]:
        stmt = select(Batch).where(Batch.product_id == product_id).order_by(Batch.created_at.asc())
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows)


__all__ = ["BatchRepository"]
