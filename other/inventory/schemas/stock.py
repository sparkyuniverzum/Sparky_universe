from __future__ import annotations
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator

from app.core.decimal_utils import q2, q3


class StockBatch(BaseModel):
    id: str
    product_id: str
    public_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    qty: Decimal
    unit_cost: Optional[Decimal] = None
    value: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("qty", mode="before")
    @classmethod
    def _q_qty(cls, v):
        return q3(v)

    @field_validator("unit_cost", mode="before")
    @classmethod
    def _q_price(cls, v):
        return None if v is None else q2(v)

    @field_validator("value", mode="before")
    @classmethod
    def _q_value(cls, v):
        return None if v is None else q2(v)


class StockProduct(BaseModel):
    product_id: str
    qty_total: Decimal
    reorder_point: Optional[Decimal] = None
    reorder_qty: Optional[Decimal] = None
    batches: List[StockBatch] = []
    value_total: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("qty_total", mode="before")
    @classmethod
    def _q_qty_total(cls, v):
        return q3(v)

    @field_validator("reorder_point", "reorder_qty", mode="before")
    @classmethod
    def _q_reorder(cls, v):
        return None if v is None else q3(v)


class Stock(BaseModel):
    items: List[StockProduct] = []


class PageMeta(BaseModel):
    total: int


class PaginatedStockList(BaseModel):
    data: List[StockProduct]
    meta: PageMeta


__all__ = ["StockBatch", "StockProduct", "Stock", "PageMeta", "PaginatedStockList"]
