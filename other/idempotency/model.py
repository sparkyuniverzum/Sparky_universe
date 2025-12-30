from __future__ import annotations
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Integer, Text, UniqueConstraint, func
from app.core.db.db_base import Base, uuid_column


class IdempotencyLog(Base):
    __tablename__ = "idempotency_logs"
    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id: Mapped[str] = uuid_column(primary_key=True)
    idem_key: Mapped[str] = mapped_column(String(128), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    resource: Mapped[str] = mapped_column(String(255), nullable=False)

    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("idem_key", "method", "resource", name="uq_idem_key_scope"),
    )


__all__ = ["IdempotencyLog", "IdempotencyKey"]
