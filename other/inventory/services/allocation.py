from __future__ import annotations

from decimal import Decimal
from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.inventory.models.stock_batch import Batch
from app.domains.inventory.models.stock_movement import MovementType
from app.domains.inventory.schemas.stock_movement import StockMovement as StockMovementOut, StockMovementCreate
from app.domains.inventory.services.stock_movement_service import create_movement

Q3 = Decimal("0.001")


class InsufficientStock(Exception):
    """Nedostatek zásob pro alokaci."""


async def _load_batches_for_allocation(db: AsyncSession, product_id: str) -> list[Batch]:
    stmt = (
        select(Batch)
        .where(Batch.product_id == product_id)
        .where(Batch.qty_in > Batch.qty_sold)
        .order_by(Batch.created_at.asc(), Batch.id.asc())
        .with_for_update()
    )
    return list((await db.execute(stmt)).scalars().all())


async def plan_allocation_fifo(db: AsyncSession, *, product_id: str, qty: Decimal) -> list[tuple[Batch, Decimal]]:
    """Naplánuje alokaci FIFO; vyhodí InsufficientStock, pokud zásoba nestačí."""
    left = Decimal(str(qty)).quantize(Q3)
    batches = await _load_batches_for_allocation(db, product_id)
    plan: list[tuple[Batch, Decimal]] = []

    for batch in batches:
        if left <= 0:
            break
        available = (batch.qty_in - batch.qty_sold).quantize(Q3)
        if available <= 0:
            continue
        take = available if available <= left else left
        plan.append((batch, take))
        left = (left - take).quantize(Q3)

    if left > 0:
        raise InsufficientStock(f"Not enough stock for product {product_id}")
    return plan


async def apply_allocation_movements(
    db: AsyncSession,
    *,
    sale_id: str,
    product_id: str,
    qty: Decimal,
) -> List[StockMovementOut]:
    """Vytvoří OUT pohyby podle FIFO plánu a vrátí je s kladnými qty."""
    plan = await plan_allocation_fifo(db, product_id=product_id, qty=qty)
    movements: List[StockMovementOut] = []

    for batch, take in plan:
        mv = await create_movement(
            db,
            StockMovementCreate(
                product_id=product_id,
                batch_id=str(batch.id),
                sale_id=sale_id,
                qty=take,
                type=MovementType.OUT,
                note="sale allocation",
            ),
        )
        movements.append(mv.model_copy(update={"qty": abs(Decimal(str(mv.qty))) }))

    return movements


async def allocate_sale_item(
    db: AsyncSession, *, sale_id: str, product_id: str, qty: Decimal
) -> List[StockMovementOut]:
    """Veřejný helper pro služby prodeje/POS."""
    return await apply_allocation_movements(db, sale_id=sale_id, product_id=product_id, qty=qty)


__all__ = [
    "InsufficientStock",
    "plan_allocation_fifo",
    "apply_allocation_movements",
    "allocate_sale_item",
]
