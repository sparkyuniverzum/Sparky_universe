from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.db_base import Base, uuid_column


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[str] = uuid_column()
    document_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True, index=True)
    supplier_id: Mapped[Optional[str]] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    partner_id: Mapped[Optional[str]] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("partners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    currency: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="CZK",
        server_default="CZK",
    )
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(12, 6, asdecimal=True),
        nullable=False,
        default=Decimal("1.000000"),
        server_default="1.000000",
    )
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    items: Mapped[List["ReceiptItem"]] = relationship(
        "ReceiptItem",
        back_populates="receipt",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ReceiptItem.id",
    )


class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[str] = uuid_column()
    receipt_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("receipts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_sku: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3, asdecimal=True),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 3, asdecimal=True),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000",
    )
    vat_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2, asdecimal=True), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category_id: Mapped[Optional[str]] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    receipt: Mapped["Receipt"] = relationship("Receipt", back_populates="items", lazy="selectin")


ReceiptItem.__table_args__ = (
    UniqueConstraint(
        "receipt_id",
        "supplier_sku",
        name="uq_receipt_item_supplier_sku_per_receipt",
    ),
)


__all__ = ["Receipt", "ReceiptItem"]
