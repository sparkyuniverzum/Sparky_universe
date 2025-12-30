from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db.db_base import Base, uuid_column


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[str] = uuid_column()

    label: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    product_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    warehouse_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    qty_in: Mapped[Decimal] = mapped_column(
        Numeric(12, 3, asdecimal=True),
        nullable=False,
        server_default="0.000",
    )

    qty_sold: Mapped[Decimal] = mapped_column(
        Numeric(12, 3, asdecimal=True),
        nullable=False,
        server_default="0.000",
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 4, asdecimal=True),
        nullable=False,
        default=Decimal("0.0000"),
        server_default="0.0000",
    )

    receipt_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("receipts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


__all__ = ["Batch"]
