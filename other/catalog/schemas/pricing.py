from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.api.schemas.common import DetailResponse, ListResponse


class PriceListCreate(BaseModel):
    name: str = Field(..., min_length=1)
    currency: str = Field(default="CZK", min_length=1, max_length=8)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: bool = True


class PriceListUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    currency: Optional[str] = Field(default=None, min_length=1, max_length=8)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: Optional[bool] = None


class PriceList(BaseModel):
    id: str
    name: str
    currency: str
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PriceListOut(PriceList):
    pass


class PriceListList(BaseModel):
    items: List[PriceListOut]
    total: int


class PriceListListResponse(ListResponse[PriceListOut]):
    pass


class PriceListDetailResponse(DetailResponse[PriceListOut]):
    pass


class ProductPrice(BaseModel):
    id: str
    price_list_id: str
    product_id: str
    unit_price: Decimal
    vat_rate: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


__all__ = [
    "PriceList",
    "PriceListCreate",
    "PriceListUpdate",
    "PriceListOut",
    "PriceListList",
    "PriceListListResponse",
    "PriceListDetailResponse",
    "ProductPrice",
]
