from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.db_base import Base, uuid_column
from app.domains.catalog.models.category import ProductCategory


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = uuid_column()
    public_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="ks")
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    vat_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2, asdecimal=True),
        nullable=False,
        default=Decimal("21.00"),
        server_default="21.00",
    )
    reorder_point: Mapped[Decimal] = mapped_column(
        Numeric(12, 3, asdecimal=True),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000",
    )
    reorder_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3, asdecimal=True),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000",
    )
    category_id: Mapped[Optional[str]] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category_rel = relationship("ProductCategory", lazy="joined")
    category_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    sku: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, unique=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, unique=True)
    supplier_id: Mapped[Optional[str]] = mapped_column(PG_UUID(as_uuid=False), nullable=True, index=True)
    supplier_sku: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    qr_payload: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    qr_image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    @property
    def category_name(self) -> Optional[str]:
        try:
            return getattr(self, "category_rel").name  # type: ignore[attr-defined]
        except Exception:
            return None

    @property
    def category(self) -> Optional[str]:
        if self.category_code:
            return self.category_code
        try:
            return getattr(self, "category_rel").code  # type: ignore[attr-defined]
        except Exception:
            return None

    __table_args__ = (
        Index("ix_products_name_trgm", "name"),
        Index("ix_products_supplier_sku_composite", "supplier_id", "supplier_sku"),
    )


class ProductPrice(Base):
    __tablename__ = "product_prices"

    id: Mapped[str] = uuid_column()
    price_list_id: Mapped[str] = mapped_column(ForeignKey("price_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2, asdecimal=True), nullable=False)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2, asdecimal=True), nullable=False, default=Decimal("21.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("ix_product_prices_price_list_product", "price_list_id", "product_id"),
    )


__all__ = ["Product", "ProductCategory", "ProductPrice"]
