from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Numeric, DateTime, ForeignKey, Enum as SAEnum, func, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.db_base import Base, uuid_column


class MovementType(PyEnum):
    # hlavní trojice – přesně tohle máš v alembicu a ve schematu
    IN = "IN"
    OUT = "OUT"
    ADJUST = "ADJUST"
    # kvůli starému kódu z receipts v původním zipu:
    RECEIPT = "IN"  # alias, aby import MovementType.RECEIPT fungoval

    # pokud bys někdy chtěl sale_allocate apod., dá se přidat jako alias na OUT/IN


class StockMovement(Base):
    __tablename__ = "stock_movements"

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
    sale_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("sales.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    warehouse_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Enum uložený v DB
    type: Mapped[MovementType] = mapped_column(
        SAEnum(MovementType, name="movement_type"),
        nullable=False,
    )

    qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3, asdecimal=True),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(64), nullable=True)


__all__ = ["StockMovement", "MovementType"]
