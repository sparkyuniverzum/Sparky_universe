from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.decimal_utils import q2, q3


class ReceiptItemBase(BaseModel):
    product_id: str | UUID | None = None
    supplier_sku: str | None = None
    product_name: str | None = None
    qty: Decimal
    unit_price: Decimal
    vat_rate: Decimal | None = None
    note: str | None = None
    category: str | None = None
    category_id: str | UUID | None = None

    @field_validator("qty", mode="before")
    @classmethod
    def _v_qty(cls, v):
        return q3(v)

    @field_validator("unit_price", "vat_rate", mode="before")
    @classmethod
    def _v_money(cls, v):
        if v is None:
            return None
        return q2(v)

    @field_validator("product_id", mode="before")
    @classmethod
    def _product_id_to_str(cls, v):
        if v is None:
            return None
        return str(v)

    @field_validator("category_id", mode="before")
    @classmethod
    def _category_id_to_str(cls, v):
        if v is None:
            return None
        return str(v)


class ReceiptItemCreate(ReceiptItemBase):
    unit: str | None = "ks"
    barcode: str | None = None

    @field_validator("product_name")
    @classmethod
    def _strip_product_name(cls, v: str | None):
        if v is None:
            return v
        value = v.strip()
        return value or None

    @field_validator("unit")
    @classmethod
    def _normalize_unit(cls, v: str | None):
        if v is None:
            return "ks"
        return v.strip() or "ks"

    @field_validator("barcode")
    @classmethod
    def _normalize_barcode(cls, v: str | None):
        if v is None:
            return None
        value = v.strip()
        return value or None

    @field_validator("category")
    @classmethod
    def _normalize_category(cls, v: str | None):
        if v is None:
            return None
        value = v.strip()
        return value or None

    @model_validator(mode="after")
    def _ensure_product_ref(self):
        if not self.product_id and not self.product_name:
            raise ValueError("product_name is required when product_id is missing")
        return self


class ReceiptItem(ReceiptItemBase):
    id: str
    created_at: datetime

    @field_validator("product_id", mode="before")
    @classmethod
    def _product_id_to_str(cls, v):
        if v is None:
            return None
        return str(v)

    model_config = ConfigDict(from_attributes=True)


class ReceiptBase(BaseModel):
    supplier_id: str | None = None
    partner_id: str | None = None
    note: str | None = None
    status: str | None = None
    currency: str | None = None
    exchange_rate: Decimal | None = None


class ReceiptCreate(ReceiptBase):
    items: List[ReceiptItemCreate] = []


class Receipt(ReceiptBase):
    id: str
    document_number: str | None = None
    created_at: datetime
    items: List[ReceiptItem] = []

    model_config = ConfigDict(from_attributes=True)

    model_config = ConfigDict(from_attributes=True)


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class ReceiptListResponse(BaseModel):
    data: List[Receipt]
    meta: PageMeta


__all__ = [
    "Receipt",
    "ReceiptCreate",
    "ReceiptItem",
    "ReceiptItemCreate",
    "ReceiptListResponse",
    "PageMeta",
]
