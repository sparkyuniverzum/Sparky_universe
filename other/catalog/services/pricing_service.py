from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.catalog.repositories.pricing_repository import PriceListRepository
from app.domains.catalog.schemas.pricing import (
    PriceListDetailResponse,
    PriceListList,
    PriceListListResponse,
    PriceListCreate,
    PriceListOut,
    PriceListUpdate,
)


async def list_price_lists(db: AsyncSession, *, limit: int, offset: int) -> PriceListList:
    repo = PriceListRepository(db)
    rows, total = await repo.list(limit=limit, offset=offset, active_only=False)
    items = [PriceListOut.model_validate(r, from_attributes=True) for r in rows]
    return PriceListList(items=items, total=total)


async def get_price_list(db: AsyncSession, price_list_id: str) -> Optional[PriceListOut]:
    repo = PriceListRepository(db)
    row = await repo.get(price_list_id)
    if not row:
        return None
    return PriceListOut.model_validate(row, from_attributes=True)


async def create_price_list(db: AsyncSession, payload: PriceListCreate) -> PriceListOut:
    repo = PriceListRepository(db)
    row = await repo.create(payload.model_dump())
    return PriceListOut.model_validate(row, from_attributes=True)


async def update_price_list(db: AsyncSession, price_list_id: str, payload: PriceListUpdate) -> PriceListOut:
    repo = PriceListRepository(db)
    row = await repo.update(price_list_id, payload.model_dump(exclude_unset=True))
    return PriceListOut.model_validate(row, from_attributes=True)


__all__ = [
    "list_price_lists",
    "get_price_list",
    "create_price_list",
    "update_price_list",
]
