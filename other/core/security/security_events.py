from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audit.model import AuditLog


async def _log_event(
    db: AsyncSession,
    *,
    event_type: str,
    user_id: str | None,
    ip: str | None,
    user_agent: str | None,
) -> None:
    if db is None:
        return
    try:
        payload = json.dumps(
            {
                "event": event_type,
                "ip": ip,
                "user_agent": user_agent,
                "ts": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
        )
        row = AuditLog(
            actor_id=user_id or "anonymous",
            method=event_type,
            resource="security",
            request_payload=payload,
            response_status=0,
            at=datetime.now(timezone.utc),
        )
        db.add(row)
        await db.flush()
        await db.commit()
    except Exception:
        try:
            await db.rollback()
        except Exception:
            pass


async def log_login_failed(db: AsyncSession, user_id: str | None, ip: str | None, user_agent: str | None) -> None:
    await _log_event(db, event_type="login_failed", user_id=user_id, ip=ip, user_agent=user_agent)


async def log_login_success(db: AsyncSession, user_id: str | None, ip: str | None, user_agent: str | None) -> None:
    await _log_event(db, event_type="login_success", user_id=user_id, ip=ip, user_agent=user_agent)


async def log_refresh_reuse_detected(db: AsyncSession, user_id: str | None, ip: str | None = None, user_agent: str | None = None) -> None:
    await _log_event(db, event_type="refresh_token_reuse", user_id=user_id, ip=ip, user_agent=user_agent)


async def log_session_expired(db: AsyncSession, user_id: str | None, ip: str | None = None, user_agent: str | None = None) -> None:
    await _log_event(db, event_type="session_expired", user_id=user_id, ip=ip, user_agent=user_agent)
