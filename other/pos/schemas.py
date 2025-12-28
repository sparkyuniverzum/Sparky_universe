from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class CashClosurePreview(BaseModel):
    period_start: datetime | None = None
    period_end: datetime | None = None
    total_cash: Decimal
    total_card: Decimal
    total_payments: Decimal
    payments: List[dict] = []


class CashClosureCreate(BaseModel):
    period_start: datetime | None = None
    period_end: datetime | None = None
    counted_cash: Decimal | None = None
    pos_id: str | None = None
    cashier_id: str | None = None
    register_id: str | None = None
    session_id: str | None = None


class CashRegisterBase(BaseModel):
    code: str
    name: str
    currency: str | None = "CZK"
    location: str | None = None


class CashRegisterCreate(CashRegisterBase):
    pass


class CashRegisterUpdate(BaseModel):
    name: str | None = None
    currency: str | None = None
    location: str | None = None


class CashRegisterOut(BaseModel):
    id: str
    code: str
    name: str
    currency: str
    location: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CashClosure(BaseModel):
    id: str
    number: str | None = None
    currency: str
    total_cash: Decimal
    total_card: Decimal
    total_payments: Decimal
    counted_cash: Decimal | None = None
    over_short: Decimal | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    pos_id: str | None = None
    cashier_id: str | None = None
    closed_at: datetime
    created_at: datetime
    status: str
    payments_snapshot: dict | None = None

    model_config = ConfigDict(from_attributes=True)


__all__ = ["CashClosurePreview", "CashClosureCreate", "CashClosure"]
