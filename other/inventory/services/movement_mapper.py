from __future__ import annotations

from typing import Literal

from app.core.decimal_utils import q3
from app.domains.inventory.models.stock_movement import StockMovement, MovementType
from app.domains.inventory.schemas.stock_movement import StockMovement as MovementOut

MovementLiteral = Literal["IN", "OUT", "ADJUST"]


def _enum_to_literal(e: MovementType) -> MovementLiteral:
    val = e.value if isinstance(e, MovementType) else e
    if val in ("IN", "OUT", "ADJUST"):
        return val  # type: ignore[return-value]
    return "ADJUST"  # fallback


def movement_to_schema(row: StockMovement) -> MovementOut:
    return MovementOut(
        id=row.id,
        product_id=row.product_id,
        batch_id=row.batch_id,
        qty=q3(row.qty),
        type=_enum_to_literal(row.type),
        note=row.note,
        created_at=row.created_at,
    )


def movements_to_schema(rows: list[StockMovement]) -> list[MovementOut]:
    return [movement_to_schema(r) for r in rows]


__all__ = ["movement_to_schema", "movements_to_schema"]
