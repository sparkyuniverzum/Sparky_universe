from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import DateTime, String, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db.db_base import Base, uuid_column
from app.domains.catalog.models.product import ProductPrice


class PriceList(Base):
    __tablename__ = "price_lists"

    id: Mapped[str] = uuid_column()
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CZK")
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


__all__ = ["PriceList", "ProductPrice"]
