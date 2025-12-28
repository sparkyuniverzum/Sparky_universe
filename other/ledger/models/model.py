from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, DateTime, Numeric, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db.db_base import Base, uuid_column


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[str] = uuid_column()
    product_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    batch_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    movement_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("stock_movements.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3, asdecimal=True),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(12, 3, asdecimal=True),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    warehouse_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    doc_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    doc_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        Index("ix_ledger_entries_product_created", "product_id", "created_at"),
        Index("ix_ledger_entries_batch_created", "batch_id", "created_at"),
    )


class StockLedger(Base):
    __tablename__ = "stock_ledger"

    id: Mapped[str] = uuid_column()
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id: Mapped[str | None] = mapped_column(ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True)
    sale_id: Mapped[str | None] = mapped_column(ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)
    receipt_id: Mapped[str | None] = mapped_column(ForeignKey("receipts.id", ondelete="SET NULL"), nullable=True, index=True)
    movement_id: Mapped[str | None] = mapped_column(ForeignKey("stock_movements.id", ondelete="CASCADE"), nullable=True, unique=True)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)  # IN/OUT/ADJUST
    qty: Mapped[Decimal] = mapped_column(Numeric(12, 3, asdecimal=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


__all__ = ["LedgerEntry", "StockLedger"]
