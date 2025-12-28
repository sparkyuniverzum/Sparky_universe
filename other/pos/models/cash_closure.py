from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.db.db_base import Base, uuid_column


class CashClosure(Base):
    __tablename__ = "cash_closures"

    id: Mapped[str] = uuid_column()
    number: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CZK", server_default="CZK")
    total_cash: Mapped[Decimal] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=False, default=Decimal("0.00"), server_default="0.00")
    total_card: Mapped[Decimal] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=False, default=Decimal("0.00"), server_default="0.00")
    total_payments: Mapped[Decimal] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=False, default=Decimal("0.00"), server_default="0.00")
    counted_cash: Mapped[Decimal | None] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=True)
    over_short: Mapped[Decimal | None] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=True)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cashier_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=False), nullable=True, index=True)
    pos_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    register_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=False), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=False), nullable=True, index=True)
    payments_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="closed", server_default="closed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


__all__ = ["CashClosure"]
