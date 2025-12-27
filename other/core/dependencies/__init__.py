from __future__ import annotations

from fastapi import Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_session as _get_session, get_session_one as _get_session_one
from app.domains.users.model import User, UserRole

# Public API reexport pro permissions
# --- auth placeholders -------------------------------------------------------

async def api_key_auth(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_api_key_alt: str | None = Header(default=None, alias="x-api-key"),
    x_api_key_dev: str | None = Header(default=None, alias="x-api-key-dev"),
) -> None:
    # placeholder: no authentication
    return None


async def get_current_user() -> User | None:
    return None


def require_roles(*roles: str):
    async def _dep(current_user: User | None = None) -> User | None:  # type: ignore[override]
        return current_user

    return _dep


require_admin = require_roles(UserRole.ADMIN)


# --- misc headers ------------------------------------------------------------

async def actor_id_dep(
    x_actor_id: str | None = Header(default=None, alias="X-Actor-Id"),
) -> str | None:
    return (x_actor_id or "").strip() or None


async def idem_key_dep(
    idem_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str | None:
    return (idem_key or "").strip() or None


# --- DB session passthrough --------------------------------------------------

async def get_session():
    # FastAPI dependency (async generator)
    async for sess in _get_session():
        yield sess


async def get_session_one() -> AsyncSession:
    return await _get_session_one()
