from __future__ import annotations
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.core.decimal_utils import q2, q3


class PosScanRequest(BaseModel):
    code: str = Field(
        ..., description="Scanned code: barcode or internal SKU or supplier SKU"
    )
    supplier_id: Optional[str] = Field(
        None, description="Supplier UUIDv7", json_schema_extra={"format": "uuid"}
    )


class PosScanResult(BaseModel):
    product_id: str = Field(
        ..., description="UUIDv7 of product", json_schema_extra={"format": "uuid"}
    )
    name: str
    price: str
    vat_rate: str


class CheckoutItemIn(BaseModel):
    product_id: str = Field(..., json_schema_extra={"format": "uuid"})
    qty: Decimal

    @field_validator("qty", mode="before")
    @classmethod
    def _v_qty(cls, v):
        return q3(v)


class CheckoutPaymentIn(BaseModel):
    type: str
    amount: Decimal
    reference: Optional[str] = None

    @field_validator("amount", mode="before")
    @classmethod
    def _v_amount(cls, v):
        return q2(v)


class CheckoutRequest(BaseModel):
    items: List[CheckoutItemIn]
    payments: Optional[List[CheckoutPaymentIn]] = None
    customer_name: Optional[str] = None
    note: Optional[str] = None


# Výstup účtenky = Sale + Payments (re-use existujících schémat)
from app.domains.sales.schemas.sale import Sale as SaleOut
from app.domains.payments.schema import Payment as PaymentOut
from app.domains.pos.models import CashClosure


class PosReceipt(BaseModel):
    sale: SaleOut
    payments: List[PaymentOut] = []
    model_config = ConfigDict(from_attributes=True)


class CashClosureOut(BaseModel):
    id: str
    number: str | None = None
    currency: str
    total_cash: Decimal
    total_card: Decimal
    closed_at: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "PosScanRequest",
    "PosScanResult",
    "CheckoutItemIn",
    "CheckoutPaymentIn",
    "CheckoutRequest",
    "PosReceipt",
    "CashClosureOut",
]
