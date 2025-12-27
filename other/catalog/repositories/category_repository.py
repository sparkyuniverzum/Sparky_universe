from __future__ import annotations

from typing import Iterable, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.repository import BaseRepository
from app.domains.catalog.models.category import ProductCategory


class ProductCategoryRepository(BaseRepository):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def list_all(self) -> List[ProductCategory]:
        rows = await self.db.execute(select(ProductCategory).order_by(ProductCategory.name))
        return list(rows.scalars().all())

    async def get(self, category_id: str) -> ProductCategory | None:
        return await self.db.get(ProductCategory, category_id)

    async def get_by_code(self, code: str) -> ProductCategory | None:
        row = await self.db.execute(select(ProductCategory).where(ProductCategory.code == code))
        return row.scalars().first()

    async def create(self, data: dict) -> ProductCategory:
        row = ProductCategory(
            code=data["code"],
            name=data["name"],
        )
        return await self.add_and_refresh(row)

    async def create_many_if_missing(self, items: Iterable[Tuple[str, str]]) -> None:
        existing = await self.list_all()
        existing_codes = {c.code for c in existing}
        for code, name in items:
            if code in existing_codes:
                continue
            self.db.add(ProductCategory(code=code, name=name))
        await self.db.flush()
