from __future__ import annotations

from enum import Enum
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.decimal_utils import q3


class MovementType(str, Enum):
    IN = "IN"
    OUT = "OUT"
    ADJUST = "ADJUST"


class StockMovementCreate(BaseModel):
    product_id: str
    qty: Decimal
    type: MovementType
    batch_id: str | None = None
    sale_id: str | None = None
    warehouse_id: str | None = None
    note: str | None = None
    reason: str | None = None

    @field_validator("qty", mode="before")
    @classmethod
    def _v_qty(cls, v):
        return q3(v)


class StockMovement(BaseModel):
    id: str
    product_id: str
    qty: Decimal
    type: MovementType
    batch_id: str | None = None
    sale_id: str | None = None
    warehouse_id: str | None = None
    note: str | None = None
    reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PageMeta(BaseModel):
    total: int


class PaginatedMovementList(BaseModel):
    data: List[StockMovement]
    meta: PageMeta


__all__ = [
    "MovementType",
    "StockMovementCreate",
    "StockMovement",
    "PageMeta",
    "PaginatedMovementList",
]
