from __future__ import annotations

from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import Any, List

from fastapi import status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.domains.catalog.models.product import Product
from app.domains.inventory.services.allocation import allocate_sale_item, InsufficientStock
from app.domains.payments.model import Payment
from app.domains.payments.schema import PaymentCreate, Payment as PaymentOut
from app.domains.payments.service import add_payment, get_payments_by_sale
from app.domains.payments.status import PaymentStatus
from app.domains.pos.models import CashClosure
from app.domains.pos.schemas import CashClosurePreview, CashClosureCreate, CashClosure as CashClosureSchema
from app.domains.accounting.service import generate_document_number
from app.core.errors import DomainError
from app.domains.pos.models.cash_drawer_session import CashDrawerSession
from app.domains.pos.models.cash_register import CashRegister
from app.domains.pos.models.cash_transaction import CashTransaction
from app.domains.pos.schema import PosScanRequest, PosScanResult, CheckoutRequest, PosReceipt
from app.domains.pos.schemas import CashRegisterCreate, CashRegisterUpdate, CashRegisterOut
from app.domains.sales.schemas.sale import SaleCreate, SaleItemCreate, Sale as SaleOut
from app.domains.sales.services.sale_service import get_sale
from app.domains.sales.repositories.sales_repository import SalesCRUD
from app.domains.suppliers.model import ProductSupplierMap
from app.core.idempotency import execute_idempotent
from app.api.schemas.common import make_detail_response


async def _default_period(db: AsyncSession) -> tuple[datetime | None, datetime | None]:
    last = (
        await db.execute(select(CashClosure).order_by(desc(CashClosure.period_end), desc(CashClosure.closed_at)).limit(1))
    ).scalar_one_or_none()
    start = getattr(last, "period_end", None) or getattr(last, "closed_at", None)
    end = None
    return start, end


async def preview_closure(db: AsyncSession, *, period_start: datetime | None = None, period_end: datetime | None = None, use_last_period: bool = True) -> CashClosurePreview:
    if use_last_period and not period_start and not period_end:
        period_start, period_end = await _default_period(db)
    filters = [Payment.cash_closure_id.is_(None), Payment.status == PaymentStatus.POSTED]
    if period_start:
        filters.append(Payment.created_at >= period_start)
    if period_end:
        filters.append(Payment.created_at <= period_end)

    stmt = select(Payment).where(and_(*filters))
    rows = (await db.execute(stmt)).scalars().all()

    total_cash = Decimal("0.00")
    total_card = Decimal("0.00")
    payments_data: List[dict] = []
    for p in rows:
        amt = Decimal(str(p.amount))
        if p.type == "cash":
            total_cash += amt
        else:
            total_card += amt
        payments_data.append({"id": str(p.id), "type": p.type, "amount": str(p.amount), "created_at": p.created_at.isoformat() if p.created_at else None})

    total_payments = total_cash + total_card
    return CashClosurePreview(
        period_start=period_start,
        period_end=period_end,
        total_cash=total_cash,
        total_card=total_card,
        total_payments=total_payments,
        payments=payments_data,
    )


async def create_closure(db: AsyncSession, payload: CashClosureCreate) -> CashClosureSchema:
    preview = await preview_closure(db, period_start=payload.period_start, period_end=payload.period_end, use_last_period=True)
    if Decimal(preview.total_cash) == Decimal("0") and Decimal(preview.total_card) == Decimal("0"):
        raise DomainError("no payments to close", status_code=400, code="closure_empty")

    session_id = payload.session_id
    if not session_id and payload.register_id:
        open_session_row = (
            await db.execute(
                select(CashDrawerSession).where(
                    CashDrawerSession.register_id == payload.register_id,
                    CashDrawerSession.status == "open",
                )
            )
        ).scalar_one_or_none()
        session_id = getattr(open_session_row, "id", None)

    number = await generate_document_number(db, code="CASHCLOSE")
    counted_cash = Decimal(str(payload.counted_cash)) if payload.counted_cash is not None else None
    over_short = None
    if counted_cash is not None:
        over_short = counted_cash - Decimal(preview.total_cash)

    closure = CashClosure(
        number=number,
        currency="CZK",
        total_cash=preview.total_cash,
        total_card=preview.total_card,
        total_payments=preview.total_payments,
        counted_cash=counted_cash,
        over_short=over_short,
        period_start=payload.period_start or preview.period_start,
        period_end=payload.period_end or preview.period_end or datetime.now(timezone.utc),
        cashier_id=payload.cashier_id,
        pos_id=payload.pos_id,
        register_id=payload.register_id,
        session_id=session_id,
        status="closed",
        payments_snapshot={"payments": preview.payments},
    )
    db.add(closure)
    await db.flush()

    # attach payments
    filters = [Payment.cash_closure_id.is_(None), Payment.status == PaymentStatus.POSTED]
    if payload.period_start:
        filters.append(Payment.created_at >= payload.period_start)
    if payload.period_end:
        filters.append(Payment.created_at <= payload.period_end)
    attach_stmt = select(Payment).where(and_(*filters))
    payments = (await db.execute(attach_stmt)).scalars().all()
    for p in payments:
        p.cash_closure_id = closure.id
        p.cash_register_id = payload.register_id or p.cash_register_id
        p.cash_session_id = session_id or p.cash_session_id
        db.add(p)

    await db.flush()
    await db.refresh(closure)
    return CashClosureSchema.model_validate(closure)


async def open_session(db: AsyncSession, *, register_code: str, opening_float: Decimal = Decimal("0.00"), cashier_id: str | None = None, note: str | None = None) -> CashDrawerSession:
    if opening_float < Decimal("0"):
        raise DomainError("opening_float must be non-negative", status_code=400, code="invalid_opening_float")

    reg = (await db.execute(select(CashRegister).where(CashRegister.code == register_code))).scalar_one_or_none()
    if not reg:
        raise DomainError("register not found", status_code=404, code="register_not_found")
    existing = (
        await db.execute(
            select(CashDrawerSession).where(
                CashDrawerSession.register_id == reg.id,
                CashDrawerSession.status == "open",
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise DomainError("session already open", status_code=400, code="session_open")

    session = CashDrawerSession(
        register_id=reg.id,
        cashier_id=cashier_id,
        opening_float=opening_float,
        status="open",
        note=note,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def close_session(db: AsyncSession, session_id: str, *, closing_float: Decimal | None = None, note: str | None = None) -> CashDrawerSession:
    session = await db.get(CashDrawerSession, session_id)
    if not session:
        raise DomainError("session not found", status_code=404, code="session_not_found")
    if getattr(session, "status", "") == "closed":
        return session
    if closing_float is not None and closing_float < Decimal("0"):
        raise DomainError("closing_float must be non-negative", status_code=400, code="invalid_closing_float")
    session.status = "closed"
    session.closing_float = closing_float
    session.closed_at = datetime.now(timezone.utc)
    if note:
        session.note = note
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def record_cash_transaction(db: AsyncSession, session_id: str, *, tx_type: str, amount: Decimal, reason: str | None = None) -> CashTransaction:
    if tx_type not in {"pay_in", "pay_out"}:
        raise DomainError("invalid transaction type", status_code=400, code="invalid_tx_type")
    session = await db.get(CashDrawerSession, session_id)
    if not session or getattr(session, "status", "") != "open":
        raise DomainError("session not open", status_code=400, code="session_not_open")
    if amount <= Decimal("0"):
        raise DomainError("amount must be greater than zero", status_code=400, code="invalid_amount")
    tx = CashTransaction(
        session_id=session_id,
        type=tx_type,
        amount=Decimal(str(amount)),
        reason=reason,
    )
    db.add(tx)
    await db.flush()
    await db.refresh(tx)
    return tx


async def list_registers(db: AsyncSession, *, limit: int = 50, offset: int = 0) -> tuple[list[CashRegisterOut], int]:
    stmt = select(CashRegister).order_by(CashRegister.code.asc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(select(func.count()).select_from(CashRegister))).scalar_one()
    items = [CashRegisterOut.model_validate(r) for r in rows]
    return items, total


async def get_register(db: AsyncSession, register_id: str) -> CashRegister:
    reg = await db.get(CashRegister, register_id)
    if not reg:
        raise DomainError("register not found", status_code=404, code="register_not_found")
    return reg


async def create_register(db: AsyncSession, payload: CashRegisterCreate) -> CashRegisterOut:
    exists = (
        await db.execute(select(CashRegister).where(CashRegister.code == payload.code))
    ).scalar_one_or_none()
    if exists:
        raise DomainError("register code already exists", status_code=400, code="register_exists")
    reg = CashRegister(
        code=payload.code,
        name=payload.name,
        currency=payload.currency or "CZK",
        location=payload.location,
    )
    db.add(reg)
    await db.flush()
    await db.refresh(reg)
    return CashRegisterOut.model_validate(reg)


async def update_register(db: AsyncSession, register_id: str, payload: CashRegisterUpdate) -> CashRegisterOut:
    reg = await get_register(db, register_id)
    if payload.name is not None:
        reg.name = payload.name
    if payload.currency is not None:
        reg.currency = payload.currency
    if payload.location is not None:
        reg.location = payload.location
    db.add(reg)
    await db.flush()
    await db.refresh(reg)
    return CashRegisterOut.model_validate(reg)


def _sdec_any(v: Any) -> str:
    if v is None:
        return "0"
    return str(v)


def _get_price_attr(row: Product) -> str:
    if hasattr(row, "price"):
        return "price"
    if hasattr(row, "unit_price"):
        return "unit_price"
    return "price"


def _get_vat_attr(row: Product) -> str:
    if hasattr(row, "vat_rate"):
        return "vat_rate"
    if hasattr(row, "vat"):
        return "vat"
    return "vat_rate"


async def scan_lookup(db: AsyncSession, payload: PosScanRequest) -> PosScanResult:
    code = (payload.code or "").strip()
    if not code:
        raise DomainError("code is required", status_code=422, code="validation_error")

    product = None

    res = await db.execute(select(Product).where(Product.barcode == code))
    product = res.scalar_one_or_none()

    if not product:
        res = await db.execute(select(Product).where(Product.sku == code))
        product = res.scalar_one_or_none()

    if not product and payload.supplier_id:
        q = (
            select(Product)
            .join(ProductSupplierMap, ProductSupplierMap.product_id == Product.id)
            .where(ProductSupplierMap.supplier_sku == code)
            .where(ProductSupplierMap.supplier_id == payload.supplier_id)
        )
        res = await db.execute(q)
        product = res.scalar_one_or_none()

    if not product:
        raise DomainError("Product not found", status_code=status.HTTP_404_NOT_FOUND, code="not_found")

    price_attr = _get_price_attr(product)
    vat_attr = _get_vat_attr(product)

    return PosScanResult(
        product_id=str(product.id),
        name=getattr(product, "name", "") or "",
        price=_sdec_any(getattr(product, price_attr, None)),
        vat_rate=_sdec_any(getattr(product, vat_attr, None)),
    )


async def _server_price_items(db: AsyncSession, items_in: list[CheckoutRequest.items.__args__[0]]) -> list[SaleItemCreate]:
    ids = [it.product_id for it in items_in]
    rows = ((await db.execute(select(Product).where(Product.id.in_(ids)))).scalars().all())
    by_id = {str(r.id): r for r in rows}

    out: list[SaleItemCreate] = []
    for it in items_in:
        prod = by_id.get(str(it.product_id))
        if not prod:
            raise DomainError(f"Product {it.product_id} not found", status_code=status.HTTP_404_NOT_FOUND, code="product_not_found")
        out.append(
            SaleItemCreate(
                product_id=str(prod.id),
                name=prod.name,
                qty=Decimal(str(it.qty)),
                unit_price=Decimal(str(prod.unit_price or 0)),
                vat_rate=Decimal(str(prod.vat_rate or 0)),
                note=None,
            )
        )
    return out


async def checkout(db: AsyncSession, payload: CheckoutRequest, actor_id: str | None) -> PosReceipt:
    sale_items = await _server_price_items(db, payload.items)

    subtotal = Decimal("0")
    vat_total = Decimal("0")
    for item in sale_items:
        line_subtotal = Decimal(item.qty) * Decimal(item.unit_price)
        line_vat = (line_subtotal * Decimal(item.vat_rate) / Decimal("100")).quantize(Decimal("0.01"))
        subtotal += line_subtotal
        vat_total += line_vat

    total_amount = (subtotal + vat_total).quantize(Decimal("0.01"))

    crud = SalesCRUD(db)

    try:
        sale_model = await crud.create(
            customer_name=payload.customer_name,
            note=payload.note,
            status="open",
            payment_terms="NET14",
            due_date=date.today() + timedelta(days=14),
            ar_status="open",
            subtotal=subtotal.quantize(Decimal("0.01")),
            vat_total=vat_total.quantize(Decimal("0.01")),
            total_amount=total_amount,
            paid_amount=Decimal("0.00"),
            balance_due=total_amount,
            items=sale_items,
        )
        sale_id = str(sale_model.id)

        for it in sale_items:
            try:
                mvs = await allocate_sale_item(db, sale_id=sale_id, product_id=it.product_id, qty=it.qty)
            except InsufficientStock:
                await db.rollback()
                raise DomainError("Na skladě není dost zboží", status_code=status.HTTP_409_CONFLICT, code="STOCK_NOT_ENOUGH")
            allocated_qty = sum((m.qty for m in mvs), Decimal("0"))
            if allocated_qty < it.qty:
                await db.rollback()
                raise DomainError("Na skladě není dost zboží", status_code=status.HTTP_409_CONFLICT, code="STOCK_NOT_ENOUGH")
            if any(m.qty < 0 for m in mvs):
                await db.rollback()
                raise DomainError("Záporná zásoba není povolena", status_code=status.HTTP_409_CONFLICT, code="STOCK_NEGATIVE_BLOCKED")

        if payload.payments:
            for pay in payload.payments:
                await add_payment(db, sale_id=sale_id, payload=PaymentCreate(type=pay.type, amount=pay.amount, reference=pay.reference))

        await db.commit()
    except Exception:
        await db.rollback()
        raise

    sale_out: SaleOut = await get_sale(db, sale_id)
    payments: list[PaymentOut] = await get_payments_by_sale(db, sale_id)
    return PosReceipt(sale=sale_out, payments=payments)


def _receipt_payload(receipt: PosReceipt) -> dict:
    resp = make_detail_response(receipt)
    return jsonable_encoder(resp)


async def checkout_with_idempotency(*, request, db: AsyncSession, payload: CheckoutRequest, actor_id: str | None, idempotency_key: str | None) -> tuple[int, dict]:
    async def handler() -> tuple[int, dict]:
        receipt = await checkout(db, payload, actor_id=actor_id)
        return status.HTTP_201_CREATED, _receipt_payload(receipt)

    body = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    return await execute_idempotent(request=request, db=db, idempotency_key=idempotency_key, handler=handler, body=body)
