from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LedgerEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    batch_id: Optional[str] = None
    movement_id: Optional[str] = None
    quantity: Decimal
    balance_after: Decimal
    reason: str
    reference_id: Optional[str] = None
    created_at: datetime
    warehouse_id: Optional[str] = None
    doc_type: Optional[str] = None
    doc_id: Optional[str] = None


__all__ = ["LedgerEntryOut"]
