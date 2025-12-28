from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import select, or_, func, String, cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_session
from app.core.dependencies import actor_id_dep, idem_key_dep
from app.core.dependencies.permissions import require_sales, require_owner
from app.api.schemas.common import DetailResponse, ListResponse
from app.api.responses import get_response_factory, ResponseFactory
from app.domains.catalog.schemas.product import Product  # Pydantic schema
from app.domains.catalog.models.product import Product as ProductModel
from app.domains.pos.schema import PosScanRequest, PosScanResult, CheckoutRequest, PosReceipt
from app.domains.pos.schemas import CashClosure, CashClosurePreview, CashClosureCreate, CashRegisterCreate, CashRegisterUpdate, CashRegisterOut
from app.domains.pos import service as pos_service
from app.domains.pos.service import preview_closure, create_closure, checkout_with_idempotency, list_registers, create_register, get_register, update_register


router = APIRouter()

pos_router = APIRouter(prefix="/pos", tags=["pos"], dependencies=[Depends(require_sales)])


@pos_router.get("/products", response_model=ListResponse[Product])
async def pos_products(
    q: Optional[str] = Query(None, description="fulltext: id/public_id/name/barcode; víceslovné = AND"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    stmt = select(ProductModel)
    if q:
        for tok in [t for t in q.split() if t]:
            like = f"%{tok}%"
            stmt = stmt.where(
                or_(
                    ProductModel.name.ilike(like),
                    ProductModel.barcode.ilike(like),
                    ProductModel.public_id.ilike(like),
                    cast(ProductModel.id, String).ilike(like),
                )
            )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    order_col = ProductModel.name if hasattr(ProductModel, "name") else ProductModel.id
    rows = ((await db.execute(stmt.order_by(order_col.asc()).limit(limit).offset(offset))).scalars().all())

    items: list[Product] = []
    for r in rows:
        if hasattr(Product, "model_validate"):
            items.append(Product.model_validate(r, from_attributes=True))
        else:
            items.append(Product.from_orm(r))

    payload = {
        "data": [it.model_dump(mode="json") for it in items],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }
    return responses.list(payload)


@pos_router.post("/scan", response_model=DetailResponse[PosScanResult])
async def pos_scan(
    payload: PosScanRequest,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    result = await pos_service.scan_lookup(db, payload)
    return responses.detail({"data": result.model_dump(mode="json")}, status_code=200)


@pos_router.post("/checkout", response_model=DetailResponse[PosReceipt], status_code=status.HTTP_201_CREATED)
async def pos_checkout(
    request: Request,
    response: Response,
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_session),
    actor_id: str | None = Depends(actor_id_dep),
    idem_key: str | None = Depends(idem_key_dep),
    responses: ResponseFactory = Depends(get_response_factory),
):
    status_code, body = await checkout_with_idempotency(
        request=request,
        db=db,
        payload=payload,
        actor_id=actor_id,
        idempotency_key=idem_key,
    )
    response.status_code = status_code
    return responses.detail(body, status_code=status_code)


closures_router = APIRouter(
    prefix="/cash-closures",
    tags=["cash_closures"],
    dependencies=[Depends(require_sales)],
)


@closures_router.get("/preview", response_model=DetailResponse[CashClosurePreview])
async def preview(
    period_start: str | None = Query(None),
    period_end: str | None = Query(None),
    use_last_period: bool = Query(True, description="If true, default period_start from last closure when params are empty"),
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    def _parse(dt: str | None):
        if not dt:
            return None
        from datetime import datetime
        return datetime.fromisoformat(dt)

    prev = await preview_closure(db, period_start=_parse(period_start), period_end=_parse(period_end), use_last_period=use_last_period)
    return responses.detail({"data": prev.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@closures_router.post("", response_model=DetailResponse[CashClosure], status_code=status.HTTP_201_CREATED)
async def create(
    payload: CashClosureCreate,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    closure = await create_closure(db, payload)
    await db.commit()
    return responses.detail({"data": closure.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


router.include_router(pos_router)
router.include_router(closures_router)


registers_router = APIRouter(
    prefix="/cash-registers",
    tags=["cash_registers"],
    dependencies=[Depends(require_sales)],
)


@registers_router.get("", response_model=ListResponse[CashRegisterOut])
async def list_cash_registers(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    items, total = await list_registers(db, limit=limit, offset=offset)
    payload = {"data": [it.model_dump(mode="json") for it in items], "meta": {"total": total, "limit": limit, "offset": offset}}
    return responses.list(payload)


@registers_router.post("", response_model=DetailResponse[CashRegisterOut], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_owner)])
async def create_cash_register(
    payload: CashRegisterCreate,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    reg = await create_register(db, payload)
    await db.commit()
    return responses.detail({"data": reg.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@registers_router.get("/{register_id}", response_model=DetailResponse[CashRegisterOut])
async def get_cash_register(
    register_id: str,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    reg = await get_register(db, register_id)
    return responses.detail({"data": CashRegisterOut.model_validate(reg).model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@registers_router.patch("/{register_id}", response_model=DetailResponse[CashRegisterOut], dependencies=[Depends(require_owner)])
async def update_cash_register(
    register_id: str,
    payload: CashRegisterUpdate,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    reg = await update_register(db, register_id, payload)
    await db.commit()
    return responses.detail({"data": reg.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


router.include_router(registers_router)

__all__ = ["router"]
