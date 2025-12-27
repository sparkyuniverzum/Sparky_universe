from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Iterable, Optional, Tuple

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.common import make_detail_response
from app.core.errors import DomainError
from app.core.idempotency import execute_idempotent
from app.core.settings import get_settings
from app.domains.catalog.models.product import Product
from app.domains.catalog.models.category import ProductCategory
from app.domains.catalog.repositories.category_repository import ProductCategoryRepository
from app.domains.catalog.repositories.product_repository import ProductRepository
from app.domains.catalog.schemas.product import PaginatedProductList, Product as ProductSchema, ProductCreate, ProductUpdate

from app.domains.catalog.utils.catalog_utils import classify_product_category, ensure_seed_categories
async def list_products(
    db: AsyncSession,
    *,
    q: Optional[str],
    limit: int,
    offset: int,
    only_active: Optional[bool],
) -> PaginatedProductList:
    repo = ProductRepository(db)
    rows, total = await repo.list(q=q, limit=limit, offset=offset, only_active=only_active)
    items = [repo.to_schema(r) for r in rows]
    return PaginatedProductList(items=items, total=total, limit=limit, offset=offset)


async def get_product(db: AsyncSession, product_id: str):
    repo = ProductRepository(db)
    return await repo.get_by_id_or_public(product_id)


async def get_product_detail(db: AsyncSession, product_id: str) -> ProductSchema:
    row = await get_product(db, product_id)
    if not row:
        raise DomainError("Product not found", status_code=status.HTTP_404_NOT_FOUND, code="product_not_found")
    if isinstance(row, ProductSchema):
        return row
    repo = ProductRepository(db)
    return repo.to_schema(row)


async def create_product(db: AsyncSession, payload: ProductCreate, *, actor_id: str | None = None) -> ProductSchema:
    await ensure_seed_categories(db)

    public_id = payload.public_id or uuid.uuid4().hex[:12]
    payload.public_id = public_id

    repo = ProductRepository(db)
    if await repo.get_by_public_id(public_id):
        raise DomainError("public_id already exists", status_code=status.HTTP_409_CONFLICT, code="public_id_conflict")

    if payload.barcode and await repo.get_by_barcode(payload.barcode):
        raise DomainError("barcode already exists", status_code=status.HTTP_409_CONFLICT, code="barcode_conflict")

    if payload.supplier_sku:
        existing = await repo.get_by_supplier_sku(None, payload.supplier_sku)
        if existing:
            raise DomainError(
                "supplier_sku already exists for this supplier",
                status_code=status.HTTP_409_CONFLICT,
                code="supplier_sku_conflict",
            )

    cat_repo = ProductCategoryRepository(db)
    category_code: str | None = None
    if payload.category_id:
        exists = await db.get(ProductCategory, payload.category_id)
        if not exists:
            raise DomainError("category_id not found", status_code=status.HTTP_404_NOT_FOUND, code="category_not_found")
        category_code = exists.code
    elif payload.category:
        by_code = await cat_repo.get_by_code(payload.category)
        if not by_code:
            raise DomainError("category not found", status_code=status.HTTP_404_NOT_FOUND, code="category_not_found")
        payload.category_id = str(by_code.id)
        category_code = by_code.code

    actor = actor_id or getattr(get_settings(), "dev_default_actor", None)

    data = payload.model_dump()
    if category_code:
        data["category_code"] = category_code
    data.setdefault("id", str(uuid.uuid4()))
    if actor:
        data["created_by"] = actor
        data["updated_by"] = actor
    created = await repo.create(data)
    return repo.to_schema(created)


async def update_product(
    db: AsyncSession,
    identifier: str,
    payload: ProductUpdate,
    *,
    actor_id: str | None = None,
) -> ProductSchema:
    repo = ProductRepository(db)
    current = await repo.get_by_id_or_public(identifier)
    if not current:
        raise DomainError("Product not found", status_code=status.HTTP_404_NOT_FOUND, code="product_not_found")

    if payload.barcode:
        other = await repo.get_by_barcode(payload.barcode)
        if other and str(other.id) != str(current.id):
            raise DomainError("barcode already exists", status_code=status.HTTP_409_CONFLICT, code="barcode_conflict")
    if payload.supplier_sku:
        other = await repo.get_by_supplier_sku(None, payload.supplier_sku)
        if other and str(other.id) != str(current.id):
            raise DomainError(
                "supplier_sku already exists for this supplier",
                status_code=status.HTTP_409_CONFLICT,
                code="supplier_sku_conflict",
            )

    cat_repo = ProductCategoryRepository(db)
    data = payload.model_dump(exclude_unset=True)
    category_code: str | None = None

    if "category_id" in data:
        if data["category_id"] is None:
            category_code = None
        else:
            exists = await db.get(ProductCategory, data["category_id"])
            if not exists:
                raise DomainError("category_id not found", status_code=status.HTTP_404_NOT_FOUND, code="category_not_found")
            category_code = exists.code
    elif "category" in data:
        if data["category"] is None:
            category_code = None
        else:
            by_code = await cat_repo.get_by_code(str(data["category"]))
            if not by_code:
                raise DomainError("category not found", status_code=status.HTTP_404_NOT_FOUND, code="category_not_found")
            data["category_id"] = str(by_code.id)
            category_code = by_code.code

    if "category_id" in data or "category" in data:
        data["category_code"] = category_code

    if actor_id:
        data["updated_by"] = actor_id

    updated = await repo.update(current, data)
    if not updated:
        raise DomainError("Product not found", status_code=status.HTTP_404_NOT_FOUND, code="product_not_found")
    return repo.to_schema(updated)


async def deactivate_product(db: AsyncSession, identifier: str) -> None:
    repo = ProductRepository(db)
    current = await repo.get_by_id_or_public(identifier)
    if current:
        await repo.deactivate(current)


async def get_product_by_supplier_sku(db: AsyncSession, supplier_id: str | None, supplier_sku: str) -> ProductSchema | None:
    if not supplier_sku:
        return None
    repo = ProductRepository(db)
    row = await repo.get_by_supplier_sku(supplier_id, supplier_sku)
    if not row:
        return None
    if isinstance(row, ProductSchema):
        return row
    return repo.to_schema(row)


def _encode_response(payload: object | None) -> dict:
    return jsonable_encoder(payload or {})


async def create_product_entry(
    *,
    request: Request,
    db: AsyncSession,
    payload: ProductCreate,
    idempotency_key: str | None,
) -> Tuple[int, dict]:
    async def handler() -> Tuple[int, dict]:
        actor = (request.headers.get("x-actor-id") or "").strip() or getattr(get_settings(), "dev_default_actor", None)
        created = await create_product(db, payload, actor_id=actor)
        await db.commit()
        return status.HTTP_201_CREATED, make_detail_response(created).model_dump(mode="json")

    status_code, payload = await execute_idempotent(
        request=request,
        db=db,
        idempotency_key=idempotency_key,
        handler=handler,
        body=payload.model_dump(),
    )
    return status_code, _encode_response(payload)


async def update_product_entry(
    *,
    request: Request,
    db: AsyncSession,
    product_id: str,
    payload: ProductUpdate,
    idempotency_key: str | None,
) -> Tuple[int, dict]:
    async def handler() -> Tuple[int, dict]:
        actor = (request.headers.get("x-actor-id") or "").strip() or getattr(get_settings(), "dev_default_actor", None)
        updated = await update_product(db, product_id, payload, actor_id=actor)
        await db.commit()
        return status.HTTP_200_OK, make_detail_response(updated).model_dump(mode="json")

    status_code, payload = await execute_idempotent(
        request=request,
        db=db,
        idempotency_key=idempotency_key,
        handler=handler,
        body=payload.model_dump(exclude_unset=True),
    )
    return status_code, _encode_response(payload)


async def deactivate_product_entry(
    *,
    request: Request,
    db: AsyncSession,
    product_id: str,
    idempotency_key: str | None,
) -> Tuple[int, dict]:
    async def handler() -> Tuple[int, dict]:
        await deactivate_product(db, product_id)
        row = await get_product(db, product_id)
        if row is None:
            body = make_detail_response(None).model_dump(mode="json")
        else:
            if isinstance(row, ProductSchema):
                schema = row
            else:
                schema = ProductRepository(db).to_schema(row)
            body = make_detail_response(schema).model_dump(mode="json")
        await db.commit()
        return status.HTTP_200_OK, body

    status_code, payload = await execute_idempotent(
        request=request,
        db=db,
        idempotency_key=idempotency_key,
        handler=handler,
        body=None,
    )
    if not idempotency_key:
        await db.commit()
    return status_code, _encode_response(payload)


__all__ = [
    "classify_product_category",
    "ensure_seed_categories",
    "list_products",
    "get_product",
    "get_product_detail",
    "create_product",
    "update_product",
    "deactivate_product",
    "get_product_by_supplier_sku",
    "create_product_entry",
    "update_product_entry",
    "deactivate_product_entry",
]
