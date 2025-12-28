from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.db.db_base import Base, uuid_column


class CashDrawerSession(Base):
    __tablename__ = "cash_drawer_sessions"

    id: Mapped[str] = uuid_column()
    register_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("cash_registers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cashier_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=False), nullable=True, index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opening_float: Mapped[Decimal] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=False, default=Decimal("0.00"), server_default="0.00")
    closing_float: Mapped[Decimal | None] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", server_default="open")
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


__all__ = ["CashDrawerSession"]
