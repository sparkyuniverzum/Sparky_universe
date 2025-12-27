from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.db_base import Base, uuid_column


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[str] = uuid_column()
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)


__all__ = ["ProductCategory"]
