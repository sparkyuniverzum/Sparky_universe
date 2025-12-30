from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_session
from app.core.idempotency import execute_idempotent
from app.core.dependencies.permissions import require_warehouse

from app.domains.inventory.schemas.stock_movement import StockMovement, StockMovementCreate
from app.api.schemas.common import ListResponse, DetailResponse, PageMeta
from app.api.responses import get_response_factory, ResponseFactory

from app.domains.inventory.services.stock_movement_service import create_movement, list_movements


router = APIRouter(
    prefix="/stock-movements",
    tags=["stock_movements"],
    dependencies=[Depends(require_warehouse)],
)


@router.post(
    "",
    response_model=DetailResponse[StockMovement],
    status_code=status.HTTP_201_CREATED,
)
async def post_movement(
    payload: StockMovementCreate,
    request: Request,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    async def _handler():
        out = await create_movement(db, payload)
        await db.commit()
        return status.HTTP_201_CREATED, {"data": out.model_dump(mode="json")}

    idem_key = request.headers.get("Idempotency-Key")
    status_code, payload_out = await execute_idempotent(
        request=request,
        db=db,
        idempotency_key=idem_key,
        handler=_handler,
        body=payload.model_dump(mode="json"),
    )
    return responses.detail(payload_out, status_code=status_code)


@router.get("", response_model=ListResponse[StockMovement])
async def get_movements(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    items, total = await list_movements(db, offset=offset, limit=limit)
    payload = {
        "data": [it.model_dump(mode="json") for it in items],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }
    return responses.list(payload)


__all__ = ["router"]
