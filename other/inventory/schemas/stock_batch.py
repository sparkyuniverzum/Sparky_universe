from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class BatchOut(BaseModel):
    id: str
    label: Optional[str] = None
    product_id: str
    qty_in: Decimal
    qty_sold: Decimal
    receipt_id: Optional[str] = None
    created_at: datetime

    @field_validator("product_id", mode="before")
    @classmethod
    def _product_id_to_str(cls, v):
        if v is None:
            return None
        return str(v)

    model_config = ConfigDict(from_attributes=True)


__all__ = ["BatchOut"]
