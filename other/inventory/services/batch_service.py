from __future__ import annotations

from typing import Optional, Tuple, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.inventory.repositories.batch_repo import BatchRepository
from app.domains.inventory.models.stock_batch import Batch


class BatchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BatchRepository(db)

    async def list(
        self,
        *,
        product_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Batch], int]:
        return await self.repo.list(product_id=product_id, limit=limit, offset=offset)

    async def get(self, batch_id: str) -> Batch | None:
        return await self.repo.get(batch_id)

    async def list_by_product(self, product_id: str) -> list[Batch]:
        return await self.repo.list_by_product(product_id)


__all__ = ["BatchService"]
