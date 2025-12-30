from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_session
from app.domains.inventory.models.stock_batch import Batch
from app.domains.inventory.schemas.stock_batch import BatchOut
from app.api.schemas.common import ListResponse, DetailResponse
from app.core.dependencies.permissions import require_warehouse
from app.api.responses import get_response_factory, ResponseFactory
from app.domains.inventory.repositories.batch_repo import BatchRepository

router = APIRouter(
    prefix="/batches",
    tags=["batches"],
    dependencies=[Depends(require_warehouse)],
)


@router.get("", response_model=ListResponse[BatchOut])
async def list_batches(
    limit: int = 100,
    offset: int = 0,
    product_id: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    repo = BatchRepository(db)
    rows, total = await repo.list(limit=limit, offset=offset, product_id=product_id)

    payload = {
        "data": [BatchOut.model_validate(r).model_dump(mode="json") for r in rows],
        "meta": {"total": int(total or 0), "limit": limit, "offset": offset},
    }
    return responses.list(payload)


@router.get("/{batch_id}", response_model=DetailResponse[BatchOut])
async def get_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    repo = BatchRepository(db)
    obj = await repo.get(batch_id)

    if obj is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    return responses.detail({"data": BatchOut.model_validate(obj).model_dump(mode="json")}, status_code=200)


@router.get("/by-product/{product_id}", response_model=ListResponse[BatchOut])
async def get_batches_by_product(
    product_id: str,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    repo = BatchRepository(db)
    rows = await repo.list_by_product(product_id)
    payload = {
        "data": [BatchOut.model_validate(r).model_dump(mode="json") for r in rows],
        "meta": {"total": len(rows), "limit": len(rows), "offset": 0},
    }
    return responses.list(payload)


__all__ = ["router"]
