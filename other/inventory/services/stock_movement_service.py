from __future__ import annotations

from decimal import Decimal
from typing import List, Tuple, Optional

from fastapi import status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.inventory.models.stock_movement import StockMovement as StockMovementORM, MovementType
from app.domains.inventory.models.stock_batch import Batch
from app.domains.inventory.schemas.stock_movement import StockMovementCreate, StockMovement as StockMovementOut
from app.domains.ledger.services.service import append_from_movement
from app.core.errors import DomainError


Q3 = Decimal("0.001")


async def _create_batch_for_in(
    db: AsyncSession,
    *,
    product_id: str,
    qty: Decimal,
    receipt_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
) -> str:
    """Vytvoří šarži pro příchozí zboží a vrátí její id."""
    batch = Batch(
        product_id=product_id,
        qty_in=qty,
        qty_sold=Decimal("0"),
        receipt_id=receipt_id,
        warehouse_id=warehouse_id,
    )
    db.add(batch)
    await db.flush()
    return batch.id


async def create_movement(
    db: AsyncSession,
    payload: StockMovementCreate,
) -> StockMovementOut:
    """
    Vytvoří skladový pohyb.
    - když je to IN a nemáme batch_id → automaticky založí šarži
    - OUT/ADJUST potřebuje batch_id (jinak není jasný stock kontext)
    """
    qty = Decimal(str(payload.qty)).quantize(Q3)
    mv_type = MovementType(payload.type)
    if mv_type == MovementType.IN:
        signed_qty = abs(qty)
    elif mv_type == MovementType.OUT:
        signed_qty = -abs(qty)
    else:
        signed_qty = qty

    batch_id = payload.batch_id
    if mv_type == MovementType.IN and not batch_id:
        batch_id = await _create_batch_for_in(
            db,
            product_id=payload.product_id,
            qty=qty,
            receipt_id=getattr(payload, "receipt_id", None),
            warehouse_id=payload.warehouse_id,
        )
    if mv_type in (MovementType.OUT, MovementType.ADJUST) and not batch_id:
        raise DomainError("batch_id is required for OUT/ADJUST movements", status_code=400, code="batch_required")

    locked_batch: Batch | None = None
    if batch_id:
        locked_batch = (
            (
                await db.execute(
                    select(Batch).where(Batch.id == batch_id).with_for_update()
                )
            )
            .scalars()
            .first()
        )
        if not locked_batch:
            raise DomainError("batch not found", status_code=status.HTTP_404_NOT_FOUND, code="batch_not_found")

    if locked_batch and mv_type == MovementType.OUT:
        available = (locked_batch.qty_in - locked_batch.qty_sold).quantize(Q3)
        if abs(signed_qty) > available:
            raise DomainError(
                "Na skladě není dost zboží",
                status_code=status.HTTP_409_CONFLICT,
                code="STOCK_NOT_ENOUGH",
            )

    mv = StockMovementORM(
        product_id=payload.product_id,
        batch_id=batch_id,
        sale_id=payload.sale_id,
        warehouse_id=payload.warehouse_id,
        qty=signed_qty,
        type=mv_type,
        note=payload.note,
        reason=payload.reason or mv_type.value,
    )
    db.add(mv)

    if locked_batch and mv_type in (MovementType.OUT, MovementType.ADJUST):
        current_sold = getattr(locked_batch, "qty_sold", None) or Decimal("0")
        delta = abs(signed_qty) if mv_type == MovementType.OUT else -signed_qty
        new_sold = (current_sold + delta).quantize(Q3)
        if new_sold < 0:
            new_sold = Decimal("0")
        if new_sold > locked_batch.qty_in:
            raise DomainError(
                "Nelze vydat více než je na skladě",
                status_code=status.HTTP_409_CONFLICT,
                code="STOCK_NOT_ENOUGH",
            )
        locked_batch.qty_sold = new_sold
        db.add(locked_batch)

    await append_from_movement(db, movement=mv, reason=payload.reason or mv_type.value)

    await db.flush()
    await db.refresh(mv)

    return StockMovementOut.model_validate(mv)


async def list_movements(
    db: AsyncSession,
    *,
    product_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[StockMovementOut], int]:
    stmt = select(StockMovementORM).order_by(StockMovementORM.created_at.desc())

    if product_id:
        stmt = stmt.where(StockMovementORM.product_id == product_id)

    total_stmt = select(func.count()).select_from(stmt.subquery())

    rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()
    total = (await db.execute(total_stmt)).scalar_one()

    return [StockMovementOut.model_validate(r) for r in rows], total


__all__ = ["create_movement", "list_movements", "MovementType"]
