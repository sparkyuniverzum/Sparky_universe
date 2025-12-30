from __future__ import annotations
from typing import Dict, Tuple, Optional, List
from decimal import Decimal
from sqlalchemy import select, func, literal, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.domains.catalog.models.product import Product
from app.domains.inventory.models.stock_batch import Batch
from app.domains.inventory.models.stock_movement import StockMovement as Movement, MovementType
from app.domains.inventory.schemas.stock import Stock, StockProduct, StockBatch
from app.core.decimal_utils import q3


def _resolve_col(model, names: list[str]) -> InstrumentedAttribute:
    for n in names:
        if hasattr(model, n):
            return getattr(model, n)
    raise AttributeError(f"Column not found on {model.__name__}: {names}")


async def get_stock(db: AsyncSession, *, warehouse_id: str | None = None) -> Stock:
    prod_rows = (
        await db.execute(
            select(
                Product.id,
                getattr(Product, "public_id", Product.id),
                getattr(Product, "reorder_point", literal(None)),
                getattr(Product, "reorder_qty", literal(None)),
            )
        )
    ).all()
    prod_map: Dict[str, Dict[str, Optional[Decimal | str]]] = {
        str(i): {
            "public_id": str(p),
            "reorder_point": rp,
            "reorder_qty": rq,
        }
        for i, p, rp, rq in prod_rows
    }

    batches_rows = (
        await db.execute(
            select(
                Batch.id,
                Batch.product_id,
                Batch.warehouse_id,
                getattr(Batch, "public_id", literal(None)),
                getattr(Batch, "unit_cost", literal(None)),
            ).where(Batch.warehouse_id == warehouse_id) if warehouse_id else select(
                Batch.id,
                Batch.product_id,
                Batch.warehouse_id,
                getattr(Batch, "public_id", literal(None)),
                getattr(Batch, "unit_cost", literal(None)),
            )
        )
    ).all()
    batches: Dict[str, Tuple[str, Optional[str], Optional[str], Optional[Decimal]]] = {
        str(bid): (str(pid), wh, (None if bpub is None else str(bpub)), bprice)
        for bid, pid, wh, bpub, bprice in batches_rows
    }

    col_pid = _resolve_col(Movement, ["product_id"])
    col_bid = _resolve_col(Movement, ["batch_id"])
    col_qty = _resolve_col(Movement, ["qty"])

    signed_qty = case(
        (Movement.type == MovementType.IN, func.abs(col_qty)),
        (Movement.type == MovementType.OUT, -func.abs(col_qty)),
        else_=col_qty,
    )

    base_stmt = select(col_pid, func.coalesce(func.sum(signed_qty), 0)).group_by(col_pid)
    if warehouse_id:
        base_stmt = base_stmt.where(Movement.warehouse_id == warehouse_id)
    prod_qty_rows = (await db.execute(base_stmt)).all()

    batch_stmt = (
        select(col_bid, func.coalesce(func.sum(signed_qty), 0))
        .where(col_bid.is_not(None))
        .group_by(col_bid)
    )
    if warehouse_id:
        batch_stmt = batch_stmt.where(Movement.warehouse_id == warehouse_id)
    batch_qty_rows = (await db.execute(batch_stmt)).all()

    prod_qty: Dict[str, Decimal] = {str(pid): Decimal(q) for pid, q in prod_qty_rows}
    batch_qty: Dict[str, Decimal] = {str(bid): Decimal(q) for bid, q in batch_qty_rows}

    items: list[StockProduct] = []
    for internal_pid, prod_info in prod_map.items():
        product_public_id = prod_info["public_id"]
        reorder_point = prod_info.get("reorder_point")
        reorder_qty = prod_info.get("reorder_qty")
        qty_total = prod_qty.get(internal_pid, Decimal("0"))
        product_batches: list[StockBatch] = []

        value_total = Decimal("0")
        for bid, (bpid, bwh, bpub, bprice) in batches.items():
            if bpid != internal_pid:
                continue
            bqty = batch_qty.get(bid, Decimal("0"))
            bvalue = None
            if bprice is not None:
                bvalue = Decimal(str(bprice)) * bqty
                value_total += bvalue
            product_batches.append(
                StockBatch(
                    id=bid,
                    product_id=bpid,
                    warehouse_id=bwh,
                    public_id=bpub,
                    qty=bqty,
                    unit_cost=bprice,
                    value=bvalue,
                )
            )

        items.append(
            StockProduct(
                product_id=product_public_id,
                qty_total=qty_total,
                reorder_point=reorder_point,
                reorder_qty=reorder_qty,
                value_total=value_total,
                batches=product_batches,
            )
        )

    return Stock(items=items)


async def get_low_stock(
    db: AsyncSession,
    *,
    threshold: Decimal | None = None,
    warehouse_id: str | None = None,
    limit: int = 5000,
    offset: int = 0,
) -> Tuple[List[StockProduct], int]:
    """
    Vrátí produkty s celkovou zásobou <= threshold. Pokud threshold není zadán,
    použije se per-product reorder_point (default 0).
    Paging řeší pouze Python slice, data jsou už malá a agregovaná.
    """
    stock = await get_stock(db, warehouse_id=warehouse_id)
    def _target(item: StockProduct) -> Decimal:
        if threshold is not None:
            return threshold
        return q3(getattr(item, "reorder_point", Decimal("0")) or Decimal("0"))

    # deterministické řazení: nejnižší zásoba, potom product_id
    filtered = sorted(
        (
            item
            for item in stock.items
            if (
                (threshold is not None or _target(item) > Decimal("0"))
                and item.qty_total <= _target(item)
            )
        ),
        key=lambda x: (x.qty_total, x.product_id),
    )
    total = len(filtered)
    sliced = filtered[offset : offset + limit]
    return sliced, total


__all__ = ["get_stock", "get_low_stock"]
