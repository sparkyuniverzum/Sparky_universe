from __future__ import annotations

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import secrets
import hashlib

from app.domains.users.model import User, PasswordResetToken
from app.domains.users.schema import UserCreate, UserOut
from app.core.dependencies import get_session
from app.core.security.deps import get_password_hasher, get_session_store, get_jwt_manager
from app.core.security.jwt_manager import JWTManager
from app.core.security.password_hasher import PasswordHasher
from app.core.security.session_store import SessionStore
from app.core.security.token_model import TokenPair
from app.core.security import security_events


class AuthService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_session),
        hasher: PasswordHasher = Depends(get_password_hasher),
        session_store: SessionStore = Depends(get_session_store),
        jwt_manager: JWTManager = Depends(get_jwt_manager),
    ) -> None:
        self.db = db
        self.hasher = hasher
        self.session_store = session_store
        self.jwt_manager = jwt_manager

    async def _get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def register(self, payload: UserCreate, current_user: User | None = None) -> UserOut:
        existing = await self._get_user_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )
        # Defer to router helper to keep single logic path
        from app.domains.users.router import create_user_core  # lazy import to avoid circular deps
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tenant_id required to register user",
            )
        user = await create_user_core(payload=payload, db=self.db, current_user=current_user)
        return UserOut.model_validate(user)

    async def login(self, email: str, password: str, request: Request | None = None) -> TokenPair:
        user = await self._get_user_by_email(email)
        if not user or not await self.hasher.verify(password, user.password_hash):
            await security_events.log_login_failed(
                self.db,
                user_id=str(user.id) if user else None,
                ip=request.client.host if request and request.client else None,
                user_agent=request.headers.get("user-agent") if request else None,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not getattr(user, "is_active", False):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

        session = await self.session_store.create_session(
            user_id=str(user.id), device="unknown", ip="unknown", role=getattr(user, "role", None)
        )
        tokens = await self.session_store.issue_tokens(session)
        await security_events.log_login_success(
            self.db,
            user_id=str(user.id),
            ip=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
        return tokens

    async def logout(self, session_id: str) -> None:
        await self.session_store.revoke_session(session_id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            return await self.session_store.rotate_refresh_token(refresh_token)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    async def request_password_reset(self, email: str) -> str | None:
        user = await self._get_user_by_email(email)
        # Nedáváme 404 kvůli enumeraci; pokud user není, vrátíme prázdnou odpověď
        if not user:
            return None

        # Zneplatníme staré tokeny daného usera
        await self.db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))

        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        rec = PasswordResetToken(
            user_id=str(user.id),
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(rec)
        await self.db.commit()
        return token

    async def reset_password_with_token(self, token: str, new_password: str) -> None:
        token_hash = self._hash_token(token)
        rec = (
            await self.db.execute(
                select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
            )
        ).scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if not rec or rec.used_at or rec.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )
        user = await self.db.get(User, rec.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

        user.password_hash = await self.hasher.hash(new_password)
        user.login_attempts = 0
        user.locked_until = None
        rec.used_at = now
        self.db.add_all([user, rec])
        await self.db.commit()


__all__ = ["AuthService"]
