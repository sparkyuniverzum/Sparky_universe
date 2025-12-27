from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Depends
from datetime import datetime, timezone

from app.core.security.jwt_manager import JWTManagerImpl, JWTManager
from app.core.security.password_hasher import Argon2Hasher, PasswordHasher
from app.core.security.session_store import SessionStore
from app.core.security.token_model import SessionInfo, TokenPair
from app.core.security.session_models import SessionRecord
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func
from app.core.db.database import get_session
from app.core.security import security_events


_jwt_manager: Optional[JWTManager] = None
_password_hasher: Optional[PasswordHasher] = None
_session_store: Optional[SessionStore] = None


def get_jwt_manager() -> JWTManager:
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManagerImpl()
    return _jwt_manager


def get_password_hasher() -> PasswordHasher:
    global _password_hasher
    if _password_hasher is None:
        _password_hasher = Argon2Hasher()
    return _password_hasher


class InMemorySessionStore(SessionStore):
    def __init__(self, jwt_manager: JWTManager) -> None:
        self.jwt_manager = jwt_manager
        self.sessions: dict[str, SessionInfo] = {}
        self.refresh_tokens: dict[str, str] = {}
        self.used_refresh: dict[str, str] = {}

    async def create_session(self, user_id: str, device: str, ip: str, role: str | None = None):
        session_id = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        data = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            role=role,
            created_at=now,
            updated_at=now,
            last_refresh_at=None,
        )
        self.sessions[session_id] = data
        return data

    async def get_session(self, session_id: str):
        return self.sessions.get(session_id)

    async def revoke_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)
        revoke_tokens = [rt for rt, sid in self.refresh_tokens.items() if sid == session_id]
        for rt in revoke_tokens:
            self.refresh_tokens.pop(rt, None)

    async def issue_tokens(self, session: SessionInfo):
        refresh_token = secrets.token_urlsafe(48)
        self.refresh_tokens[refresh_token] = session.session_id
        session.last_refresh_at = datetime.now(timezone.utc)
        session.updated_at = session.last_refresh_at
        access_token = await self.jwt_manager.create_access_token(
            {"sub": session.user_id, "sid": session.session_id, "role": session.role}
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def rotate_refresh_token(self, refresh_token: str):
        session_id = self.refresh_tokens.get(refresh_token)
        if not session_id:
            # reuse/invalid: if we saw it before, revoke that session id
            reused_session_id = self.used_refresh.get(refresh_token)
            if reused_session_id:
                await self.revoke_session(reused_session_id)
            raise ValueError("Invalid refresh token")
        session = await self.get_session(session_id)
        if not session:
            raise ValueError("Session expired")
        # revoke old
        self.refresh_tokens.pop(refresh_token, None)
        self.used_refresh[refresh_token] = session_id
        return await self.issue_tokens(session)

    async def touch_session(self, session_id: str) -> None:
        sess = self.sessions.get(session_id)
        if sess:
            sess.updated_at = datetime.now(timezone.utc)


def get_session_store(
    jwt_manager: JWTManager = Depends(get_jwt_manager),  # type: ignore[arg-type]
    db: AsyncSession = Depends(get_session),  # type: ignore[arg-type]
) -> SessionStore:
    global _session_store
    if db:
        return DatabaseSessionStore(db=db, jwt_manager=jwt_manager)
    if _session_store is None:
        _session_store = InMemorySessionStore(jwt_manager)
    return _session_store


class DatabaseSessionStore(SessionStore):
    def __init__(self, db: AsyncSession, jwt_manager: JWTManager) -> None:
        self.db = db
        self.jwt_manager = jwt_manager
        self._ready = False

    async def _ensure_table(self) -> None:
        if self._ready:
            return
        def create_if_needed(sync_session):
            conn = sync_session.connection()
            SessionRecord.__table__.create(bind=conn, checkfirst=True)

        await self.db.run_sync(create_if_needed)
        self._ready = True

    def _hash_refresh(self, refresh_token: str) -> str:
        import hashlib

        return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()

    async def create_session(self, user_id: str, device: str, ip: str, role: str | None = None):
        await self._ensure_table()
        session_id = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        rec = SessionRecord(
            session_id=session_id,
            user_id=user_id,
            role=role,
            device=device,
            ip=ip,
            created_at=now,
            updated_at=now,
        )
        self.db.add(rec)
        await self.db.flush()
        await self.db.commit()
        return SessionInfo(session_id=session_id, user_id=user_id, role=role, created_at=now, updated_at=now)

    async def get_session(self, session_id: str):
        await self._ensure_table()
        row = (
            await self.db.execute(select(SessionRecord).where(SessionRecord.session_id == session_id))
        ).scalar_one_or_none()
        if not row or row.revoked_at is not None:
            return None
        return SessionInfo(
            session_id=row.session_id,
            user_id=row.user_id,
            role=row.role,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_refresh_at=row.last_refresh_at,
        )

    async def revoke_session(self, session_id: str) -> None:
        await self._ensure_table()
        await self.db.execute(
            SessionRecord.__table__.delete().where(SessionRecord.session_id == session_id)
        )
        await self.db.commit()
        # in-memory cleanup handled separately

    async def issue_tokens(self, session: SessionInfo):
        await self._ensure_table()
        refresh_token = secrets.token_urlsafe(48)
        refresh_hash = self._hash_refresh(refresh_token)
        await self.db.execute(
            update(SessionRecord)
            .where(SessionRecord.session_id == session.session_id)
            .values(
                refresh_token_hash=refresh_hash,
                revoked_at=None,
                last_refresh_at=func.now(),
                updated_at=func.now(),
            )
        )
        access_token = await self.jwt_manager.create_access_token(
            {"sub": session.user_id, "sid": session.session_id, "role": session.role}
        )
        await self.db.commit()
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def rotate_refresh_token(self, refresh_token: str):
        await self._ensure_table()
        refresh_hash = self._hash_refresh(refresh_token)
        row = (
            await self.db.execute(select(SessionRecord).where(SessionRecord.refresh_token_hash == refresh_hash))
        ).scalar_one_or_none()
        if not row or row.revoked_at is not None:
            # reuse or invalid
            if row:
                await security_events.log_refresh_reuse_detected(self.db, user_id=row.user_id)
                await self.revoke_session(row.session_id)
            else:
                await security_events.log_refresh_reuse_detected(self.db, user_id=None)
            raise ValueError("Invalid refresh token")
        session = SessionInfo(
            session_id=row.session_id,
            user_id=row.user_id,
            role=row.role,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_refresh_at=row.last_refresh_at,
        )
        return await self.issue_tokens(session)

    async def touch_session(self, session_id: str) -> None:
        await self._ensure_table()
        await self.db.execute(
            update(SessionRecord)
            .where(SessionRecord.session_id == session_id)
            .values(updated_at=func.now())
        )
        await self.db.commit()
