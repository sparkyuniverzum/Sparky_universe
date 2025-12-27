from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import ResponseFactory, get_response_factory
from app.api.schemas.common import ListResponse, DetailResponse
from app.core.db.database import get_session
from app.domains.catalog.schemas.category import ProductCategory, ProductCategoryCreate
from app.domains.catalog.services import category_service as category_svc
from app.core.dependencies.permissions import require_owner

router = APIRouter(tags=["catalog"], dependencies=[Depends(require_owner)])


@router.get("/product-categories", response_model=ListResponse[ProductCategory], status_code=status.HTTP_200_OK)
async def list_categories(
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    items: List[ProductCategory] = await category_svc.list_categories(db)
    payload = {
        "data": [item.model_dump(mode="json") for item in items],
        "meta": {"total": len(items), "limit": len(items), "offset": 0},
    }
    return responses.list(payload)


@router.post("/product-categories", response_model=DetailResponse[ProductCategory], status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: ProductCategoryCreate,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    created = await category_svc.create_category(db, payload)
    return responses.detail({"data": created.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


__all__ = ["router"]
