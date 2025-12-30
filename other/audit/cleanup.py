from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.domains.audit.model import AuditLog
from app.core.db.database import get_session_one


async def cleanup_audit_logs(retention_days: int) -> None:
    """Delete audit_log rows older than retention_days."""
    db: Optional[AsyncSession] = None
    try:
        db = await get_session_one()
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        stmt = delete(AuditLog).where(AuditLog.at < cutoff)
        await db.execute(stmt)
        await db.commit()
    except Exception:
        if db:
            await db.rollback()
    finally:
        if db:
            await db.close()


async def ensure_audit_schema() -> None:
    """Deprecated: rely on Alembic migrations."""
    return None


async def audit_cleanup_worker() -> None:
    settings = get_settings()
    if str(getattr(settings, "env", "")).lower() == "test":
        return
    retention = int(getattr(settings, "audit_retention_days", 0) or 0)
    if retention <= 0:
        return
    # run once at startup, then daily
    await cleanup_audit_logs(retention)
    while True:
        await asyncio.sleep(24 * 60 * 60)
        await cleanup_audit_logs(retention)


__all__ = ["audit_cleanup_worker", "cleanup_audit_logs"]
