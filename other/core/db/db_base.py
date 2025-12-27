from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.utils import uuid7


class Base(DeclarativeBase):
    pass


def uuid_column(*, primary_key: bool = True):
    # UUIDv7 generace na aplikační i DB úrovni (fallback server_default pro raw SQL)
    return mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=primary_key,
        default=uuid7,
        server_default=text("uuid7()"),
    )
