from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ledger.models.model import LedgerEntry
from app.domains.ledger.models.balance import LedgerBalance
from app.domains.inventory.models.stock_movement import StockMovement, MovementType
from app.core.errors import DomainError


def _signed_qty(mv: StockMovement) -> Decimal:
    if mv.type == MovementType.IN:
        return abs(Decimal(str(mv.qty)))
    if mv.type == MovementType.OUT:
        return -abs(Decimal(str(mv.qty)))
    return Decimal(str(mv.qty))


async def append_from_movement(
    db: AsyncSession,
    *,
    movement: StockMovement,
    reason: str | None = None,
) -> LedgerEntry:
    # lock last balance row for this product to avoid race conditions
    last_balance = (
        await db.execute(
            select(LedgerEntry.balance_after)
            .where(LedgerEntry.product_id == movement.product_id)
            .order_by(LedgerEntry.created_at.desc())
            .limit(1)
            .with_for_update()
        )
    ).scalar_one_or_none()
    prev_balance = Decimal(str(last_balance or Decimal("0")))

    signed_qty = _signed_qty(movement)
    balance_after = prev_balance + signed_qty

    if balance_after < Decimal("0"):
        raise DomainError("negative stock not allowed", status_code=409, code="STOCK_NEGATIVE_BLOCKED")

    # upsert ledger balance row
    balance_row = (
        await db.execute(
            select(LedgerBalance).where(LedgerBalance.product_id == movement.product_id).with_for_update()
        )
    ).scalar_one_or_none()
    if balance_row:
        balance_row.balance = balance_after
        balance_row.updated_at = movement.created_at
        db.add(balance_row)
    else:
        bal = LedgerBalance(product_id=str(movement.product_id), balance=balance_after, updated_at=movement.created_at)
        db.add(bal)

    entry = LedgerEntry(
        product_id=movement.product_id,
        batch_id=getattr(movement, "batch_id", None),
        movement_id=movement.id,
        quantity=signed_qty,
        balance_after=balance_after,
        reason=reason or movement.type.value,
        reference_id=getattr(movement, "sale_id", None)
        or getattr(movement, "receipt_id", None),
        warehouse_id=getattr(movement, "warehouse_id", None),
        doc_type=movement.type.value,
        doc_id=str(getattr(movement, "id", "")),
    )
    db.add(entry)
    await db.flush()
    return entry


__all__ = ["append_from_movement"]
