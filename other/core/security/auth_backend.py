from __future__ import annotations

from typing import Any
from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException, status
from fastapi import Depends
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.model import User
from app.core.security.jwt_manager import JWTManager
from app.core.security.session_store import SessionStore
from app.core.security.deps import get_jwt_manager, get_session_store
from app.core.db.database import get_session
from app.core.security.session_service import ABSOLUTE_SESSION_LIFETIME, IDLE_SESSION_LIFETIME
from app.core.security import security_events


class AuthBackend:
    """Extract and validate access token from request"""

    def __init__(
        self,
        db: AsyncSession = Depends(get_session),
        session_store: SessionStore = Depends(get_session_store),
        jwt_manager: JWTManager = Depends(get_jwt_manager),
    ) -> None:
        self.db = db
        self.session_store = session_store
        self.jwt_manager = jwt_manager

    async def extract_token(self, request: Request) -> str | None:
        auth = request.headers.get("authorization") or ""
        if not auth.lower().startswith("bearer "):
            return None
        return auth.split(" ", 1)[1].strip() or None

    async def authenticate(self, request: Request) -> User:
        token = await self.extract_token(request)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

        try:
            payload = await self.jwt_manager.decode_access_token(token)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

        user_id = payload.get("sub") or payload.get("user_id")
        session_id = payload.get("sid") or payload.get("session_id")
        if not user_id or not session_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        session = await self.session_store.get_session(str(session_id))
        if session is None or str(session.user_id) != str(user_id):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

        now = datetime.now(timezone.utc)
        # lockout check
        user = await self.db.get(User, user_id)
        if user and user.locked_until and user.locked_until > now:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account locked")

        idle_base = session.updated_at or session.created_at
        if session.created_at + ABSOLUTE_SESSION_LIFETIME < now or idle_base + IDLE_SESSION_LIFETIME < now:
            await self.session_store.revoke_session(session.session_id)
            await security_events.log_session_expired(
                self.db,
                user_id=str(user_id),
                ip=self._client_ip(request),
                user_agent=request.headers.get("user-agent"),
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

        user = user or await self.db.get(User, user_id)
        if not user or getattr(user, "is_active", False) is False:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

        await self.session_store.touch_session(session.session_id)
        return user

    def _client_ip(self, request: Request) -> str | None:
        if request.client:
            return request.client.host
        return request.headers.get("x-forwarded-for")

