from __future__ import annotations

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domains.catalog.repositories.category_repository import ProductCategoryRepository
from app.domains.catalog.schemas.category import ProductCategory, ProductCategoryCreate


async def list_categories(db: AsyncSession) -> list[ProductCategory]:
    repo = ProductCategoryRepository(db)
    rows = await repo.list_all()
    return [ProductCategory.model_validate(r, from_attributes=True) for r in rows]


async def create_category(db: AsyncSession, payload: ProductCategoryCreate) -> ProductCategory:
    repo = ProductCategoryRepository(db)
    if await repo.get_by_code(payload.code):
        raise DomainError(
            "Category code already exists",
            status_code=status.HTTP_409_CONFLICT,
            code="category_conflict",
        )
    row = await repo.create(payload.model_dump())
    return ProductCategory.model_validate(row, from_attributes=True)


__all__ = ["list_categories", "create_category"]
