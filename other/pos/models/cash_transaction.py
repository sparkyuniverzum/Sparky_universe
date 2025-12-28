from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.db.db_base import Base, uuid_column


class CashTransaction(Base):
    __tablename__ = "cash_transactions"

    id: Mapped[str] = uuid_column()
    session_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("cash_drawer_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # pay_in / pay_out
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


__all__ = ["CashTransaction"]
