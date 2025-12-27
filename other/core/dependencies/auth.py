from fastapi import Depends
from starlette.requests import Request

from app.core.security.auth_backend import AuthBackend
from app.core.security.deps import get_session_store, get_jwt_manager
from app.core.dependencies import get_session_one
from app.core.settings import get_settings


async def get_current_user(request: Request):
    """Vrátí aktuálního uživatele nebo None podle nastavení a middleware."""
    settings = get_settings()
    if settings.auth_disabled or settings.dev_auth_bypass or settings.env in {"dev", "test"}:
        return None

    user = getattr(request.state, "user", None)
    if user is not None:
        return user

    db = await get_session_one()
    try:
        backend = AuthBackend(
            db=db,
            session_store=get_session_store(db=db),
            jwt_manager=get_jwt_manager(),
        )
        return await backend.authenticate(request)
    finally:
        await db.close()


__all__ = ["get_current_user"]
