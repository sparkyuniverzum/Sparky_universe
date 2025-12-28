from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from sqlalchemy import DateTime, Numeric, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.db_base import Base, uuid_column


class LedgerBalance(Base):
    """Per product running balance for fast reads."""

    __tablename__ = "ledger_balances"

    id: Mapped[str] = uuid_column()
    product_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 3, asdecimal=True), nullable=False, default=Decimal("0"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_ledger_balances_product", "product_id", unique=True),)


__all__ = ["LedgerBalance"]
