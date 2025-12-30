from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Integer, func, Index

from app.core.db.db_base import Base, uuid_column


class AuditLog(Base):
    """ORM model pro tabulku audit_log.

    Schéma odpovídá Alembic migracím 0008/0009 – tabulka se jmenuje
    `audit_log` (v jednotném čísle) a obsahuje sloupce `at`, `actor_id`,
    `method`, `resource`, `request_payload`, `response_status`.
    """

    __tablename__ = "audit_log"

    id: Mapped[str] = uuid_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # V DB jsou tyto sloupce povolené jako NULL (kvůli starším datům),
    # proto je necháváme nullable=True – aplikace je ale vždy vyplňuje.
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="anonymous", index=True)
    method: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    resource: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    request_payload: Mapped[str] = mapped_column(Text, nullable=True)
    request_headers: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", index=True)

    __table_args__ = (
        Index("ix_audit_log_at_desc", at.desc()),
    )


__all__ = ["AuditLog"]
