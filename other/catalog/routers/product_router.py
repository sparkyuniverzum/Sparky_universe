from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import ResponseFactory, get_response_factory
from app.api.schemas.common import DetailResponse, ListResponse, make_detail_response, make_list_response
from app.core.db.database import get_session
from app.core.dependencies import idem_key_dep
from app.core.dependencies.permissions import require_owner
from app.domains.catalog.services import catalog_service as svc
from app.domains.catalog.schemas.product import Product, ProductCreate, ProductUpdate
from app.domains.catalog.schemas.category import ProductCategory
from app.domains.catalog.services.qr_service import generate_product_qr

router = APIRouter(tags=["catalog"], dependencies=[Depends(require_owner)])


@router.get("/products", response_model=ListResponse[Product], status_code=status.HTTP_200_OK)
async def list_products(
    db: AsyncSession = Depends(get_session),
    q: Optional[str] = Query(None, description="Full-text: name or barcode"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    only_active: Optional[bool] = Query(None, description="Filter by is_active"),
):
    paginated = await svc.list_products(db, q=q, limit=limit, offset=offset, only_active=only_active)
    return make_list_response(
        paginated.items,
        total=paginated.total,
        limit=paginated.limit,
        offset=paginated.offset,
    )


@router.get("/products/{product_id}", response_model=DetailResponse[Product], status_code=status.HTTP_200_OK)
async def get_product(product_id: str, db: AsyncSession = Depends(get_session)):
    product = await svc.get_product_detail(db, product_id)
    return make_detail_response(product)


@router.post("/products", response_model=DetailResponse[Product], status_code=status.HTTP_201_CREATED)
async def create_product(
    request: Request,
    payload: ProductCreate,
    db: AsyncSession = Depends(get_session),
    idem_key: Optional[str] = Depends(idem_key_dep),
    responses: ResponseFactory = Depends(get_response_factory),
):
    status_code, body = await svc.create_product_entry(
        request=request,
        db=db,
        payload=payload,
        idempotency_key=idem_key,
    )
    return responses.detail(body, status_code=status_code)


@router.patch("/products/{product_id}", response_model=DetailResponse[Product], status_code=status.HTTP_200_OK)
async def update_product(
    request: Request,
    product_id: str,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_session),
    idem_key: Optional[str] = Depends(idem_key_dep),
    responses: ResponseFactory = Depends(get_response_factory),
):
    status_code, body = await svc.update_product_entry(
        request=request,
        db=db,
        product_id=product_id,
        payload=payload,
        idempotency_key=idem_key,
    )
    return responses.detail(body, status_code=status_code)


@router.delete("/products/{product_id}", response_model=DetailResponse[Product], status_code=status.HTTP_200_OK)
async def deactivate_product(
    request: Request,
    product_id: str,
    db: AsyncSession = Depends(get_session),
    idem_key: Optional[str] = Depends(idem_key_dep),
    responses: ResponseFactory = Depends(get_response_factory),
):
    status_code, body = await svc.deactivate_product_entry(
        request=request,
        db=db,
        product_id=product_id,
        idempotency_key=idem_key,
    )
    return responses.detail(body or {"data": None}, status_code=status_code)


@router.post("/products/{product_id}/qr", response_model=DetailResponse[dict], status_code=status.HTTP_201_CREATED)
async def generate_product_qr_code(
    product_id: str,
    force: bool = Query(False, description="Regenerovat QR i když existuje"),
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    data = await generate_product_qr(db, product_id, force=force)
    await db.commit()
    return responses.detail({"data": data}, status_code=status.HTTP_201_CREATED)


@router.get("/products/{product_id}/qr", response_model=DetailResponse[dict], status_code=status.HTTP_200_OK)
async def get_product_qr_code(
    product_id: str,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    repo_data = await generate_product_qr(db, product_id, force=False)
    await db.commit()
    return responses.detail({"data": repo_data}, status_code=status.HTTP_200_OK)


__all__ = ["router"]
