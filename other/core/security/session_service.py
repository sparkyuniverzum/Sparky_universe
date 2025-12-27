from __future__ import annotations

from datetime import timedelta

from fastapi import Depends, HTTPException, status, Request

from app.core.security.deps import get_session_store
from app.core.security.session_store import SessionStore
from app.core.security.token_model import TokenPair
from app.core.security import security_events

ABSOLUTE_SESSION_LIFETIME = timedelta(days=7)
IDLE_SESSION_LIFETIME = timedelta(hours=12)


class SessionService:
    def __init__(self, session_store: SessionStore = Depends(get_session_store)) -> None:
        self.session_store = session_store

    async def refresh(self, refresh_token: str, request: Request | None = None) -> TokenPair:
        ip = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
        try:
            return await self.session_store.rotate_refresh_token(refresh_token)
        except ValueError as exc:
            db = getattr(self.session_store, "db", None)
            await security_events.log_refresh_reuse_detected(db, user_id=None, ip=ip, user_agent=ua)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
