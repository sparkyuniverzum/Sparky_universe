from __future__ import annotations

from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.domains.audit.model import AuditLog
from app.domains.audit.schema import AuditLogOut
from app.api.schemas.common import ListResponse
from app.core.dependencies.permissions import require_owner
from app.api.responses import get_response_factory, ResponseFactory

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit"],
    dependencies=[Depends(require_owner)],
)


@router.get("/", response_model=ListResponse[AuditLogOut])
async def list_audit_logs(
    limit: int = 100,
    offset: int = 0,
    actor_id: str | None = None,
    method: str | None = None,
    resource: str | None = None,
    status_code: int | None = None,
    from_at: str | None = None,
    to_at: str | None = None,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
) -> dict[str, Any]:
    if limit <= 0 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be non-negative")

    def _parse_dt(val: str | None) -> datetime | None:
        if not val:
            return None
        try:
            return datetime.fromisoformat(val)
        except Exception:
            raise HTTPException(status_code=422, detail="from_at/to_at must be ISO datetime")

    from_dt = _parse_dt(from_at)
    to_dt = _parse_dt(to_at)

    filters = []
    if actor_id:
        filters.append(AuditLog.actor_id == actor_id)
    if method:
        filters.append(AuditLog.method == method)
    if resource:
        filters.append(AuditLog.resource.ilike(f"%{resource}%"))
    if status_code is not None:
        filters.append(AuditLog.response_status == status_code)
    if from_dt:
        filters.append(AuditLog.at >= from_dt)
    if to_dt:
        filters.append(AuditLog.at <= to_dt)

    stmt = select(AuditLog).order_by(AuditLog.at.desc())
    if filters:
        stmt = stmt.where(and_(*filters))
    total_stmt = select(func.count()).select_from(stmt.subquery())

    result = await db.execute(stmt.limit(limit).offset(offset))
    rows = list(result.scalars().all())
    total = (await db.execute(total_stmt)).scalar_one()

    payload = {
        "data": [AuditLogOut.model_validate(r).model_dump(mode="json") for r in rows],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }
    return responses.list(payload)


__all__ = ["router"]
