from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, UUID as UUID_TYPE

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.schemas.common import DetailResponse, ListResponse


class ProductCreate(BaseModel):
    public_id: Optional[str] = None
    name: str = Field(min_length=1)
    unit: str = Field(default="ks", min_length=1)
    unit_price: Decimal | str = Field(default="0.00")
    vat_rate: Decimal | str = Field(default="21.00")
    reorder_point: Decimal | str = Field(default="0.000")
    reorder_qty: Decimal | str = Field(default="0.000")
    category: Optional[str] = None
    category_id: Optional[UUID_TYPE | str] = None
    category_name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_sku: Optional[str] = None
    is_active: bool = True

    @field_validator("name", "unit", mode="before")
    @classmethod
    def _strip_required(cls, v):
        if v is None or str(v).strip() == "":
            raise ValueError("value is required")
        return str(v).strip()

    @field_validator("unit_price", "vat_rate", mode="before")
    @classmethod
    def _decimals(cls, v):
        if v is None or str(v).strip() == "":
            raise ValueError("value is required")
        return v


class ProductUpdate(BaseModel):
    public_id: Optional[str] = None
    name: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal | str] = None
    vat_rate: Optional[Decimal | str] = None
    reorder_point: Optional[Decimal | str] = None
    reorder_qty: Optional[Decimal | str] = None
    category: Optional[str] = None
    category_id: Optional[UUID_TYPE | str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_sku: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("name", "unit", mode="before")
    @classmethod
    def _strip_optional(cls, v):
        if v is None:
            return v
        val = str(v).strip()
        if val == "":
            raise ValueError("value cannot be empty")
        return val

    @field_validator("unit_price", "vat_rate", mode="before")
    @classmethod
    def _decimals_optional(cls, v):
        if v is None:
            return v
        if str(v).strip() == "":
            raise ValueError("value cannot be empty")
        return v


class Product(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    public_id: str
    name: str
    unit: str
    unit_price: Decimal
    vat_rate: Decimal
    reorder_point: Decimal
    reorder_qty: Decimal
    category: Optional[str] = None
    category_id: Optional[UUID_TYPE | str] = None
    category_name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_sku: Optional[str] = None
    is_active: bool
    is_archived: bool
    version: int
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PaginatedProductList(BaseModel):
    items: List[Product]
    total: int
    limit: int
    offset: int


class ProductListResponse(ListResponse[Product]):
    pass


class ProductDetailResponse(DetailResponse[Product]):
    pass


__all__ = [
    "Product",
    "ProductCreate",
    "ProductUpdate",
    "PaginatedProductList",
    "ProductListResponse",
    "ProductDetailResponse",
]
