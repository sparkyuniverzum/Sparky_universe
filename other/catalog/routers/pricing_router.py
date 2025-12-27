from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import ResponseFactory, get_response_factory
from app.api.schemas.common import DetailResponse, ListResponse
from app.core.db.database import get_session
from app.domains.catalog.services import pricing_service as svc
from app.domains.catalog.schemas.pricing import PriceListCreate, PriceListOut, PriceListUpdate
from app.core.dependencies.permissions import require_owner

router = APIRouter(tags=["pricing"], dependencies=[Depends(require_owner)])


@router.get("/price-lists", response_model=ListResponse[PriceListOut])
async def list_price_lists(
    db: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    responses: ResponseFactory = Depends(get_response_factory),
):
    result = await svc.list_price_lists(db, limit=limit, offset=offset)
    payload = {
        "data": [item.model_dump(mode="json") for item in result.items],
        "meta": {"total": result.total, "limit": limit, "offset": offset},
    }
    return responses.list(payload)


@router.get("/price-lists/{price_list_id}", response_model=DetailResponse[PriceListOut])
async def get_price_list(
    price_list_id: str,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    row = await svc.get_price_list(db, price_list_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price list not found")
    return responses.detail({"data": row.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@router.post("/price-lists", response_model=DetailResponse[PriceListOut], status_code=status.HTTP_201_CREATED)
async def create_price_list(
    payload: PriceListCreate,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    row = await svc.create_price_list(db, payload)
    await db.commit()
    return responses.detail({"data": row.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@router.patch("/price-lists/{price_list_id}", response_model=DetailResponse[PriceListOut])
async def update_price_list(
    price_list_id: str,
    payload: PriceListUpdate,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    row = await svc.update_price_list(db, price_list_id, payload)
    await db.commit()
    return responses.detail({"data": row.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


__all__ = ["router"]
