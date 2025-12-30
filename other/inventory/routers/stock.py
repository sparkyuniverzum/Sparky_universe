from __future__ import annotations
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_session
from app.domains.inventory.schemas.stock import (
    Stock as StockSchema,
    PaginatedStockList,
    PageMeta,
)
from app.api.schemas.common import DetailResponse
from app.domains.inventory.services.stock_service import get_stock, get_low_stock
from app.core.dependencies.permissions import require_warehouse
from app.api.responses import get_response_factory, ResponseFactory

router = APIRouter(
    prefix="/stock",
    tags=["stock"],
    dependencies=[Depends(require_warehouse)],
)


@router.get("", response_model=DetailResponse[StockSchema])
async def get_current_stock(
    warehouse_id: str | None = Query(None, description="Filter by warehouse/location id"),
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    stock = await get_stock(db, warehouse_id=warehouse_id)
    return responses.detail({"data": stock}, status_code=200)


@router.get("/low", response_model=PaginatedStockList)
async def get_low_stock_view(
    threshold: Decimal | None = Query(None, description="Hraniční zásoba; pokud není, použije se reorder_point"),
    limit: int = Query(5000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    warehouse_id: str | None = Query(None, description="Filter by warehouse/location id"),
    db: AsyncSession = Depends(get_session),
):
    items, total = await get_low_stock(
        db,
        threshold=threshold,
        warehouse_id=warehouse_id,
        limit=limit,
        offset=offset,
    )
    return {"data": items, "meta": PageMeta(total=total)}


__all__ = ["router"]
