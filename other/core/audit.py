# backend/app/core/audit.py
from __future__ import annotations

from typing import Callable, Awaitable, Optional, Any

from fastapi.routing import APIRoute
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session, get_session_one
from app.domains.audit.service import log_audit
from app.core.settings import get_settings


def _sanitize_headers(raw_headers: dict[str, Any]) -> dict[str, Any]:
    """Drop sensitive headers (Authorization/API keys/cookies) before audit log."""
    deny = {"authorization", "x-api-key", "cookie"}
    return {k: v for k, v in raw_headers.items() if k.lower() not in deny}


class AuditRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:  # type: ignore[override]
        original_handler = super().get_route_handler()

        async def audit_wrapper(request: Request) -> Response:
            db: AsyncSession | None = None
            try:
                db = await get_session_one()
                assert isinstance(db, AsyncSession)

                actor_id: Optional[str] = None
                try:
                    user = getattr(request.state, "user", None)
                    if user and getattr(user, "id", None):
                        actor_id = str(user.id)
                    else:
                        actor_id = request.headers.get("x-actor-id") or None
                        if actor_id:
                            actor_id = actor_id.strip() or None
                        if actor_id is None:
                            settings = get_settings()
                            actor_id = getattr(settings, "dev_default_actor", None)
                except Exception:
                    actor_id = None

                try:
                    body: Any = await request.json()
                except Exception:
                    body = None

                try:
                    response: Response = await original_handler(request)
                    status_code = response.status_code
                except Exception:
                    # log 500 with minimal info
                    status_code = 500
                    try:
                        await log_audit(
                            db=db,
                            actor_id=actor_id,
                            method=request.method,
                            resource=request.url.path,
                            request_payload=body,
                            response_status=status_code,
                            request_headers=_sanitize_headers(dict(request.headers)),
                        )
                        await db.commit()
                    except Exception:
                        await db.rollback()
                    raise

                try:
                    await log_audit(
                        db=db,
                        actor_id=actor_id,
                        method=request.method,
                        resource=request.url.path,
                        request_payload=body,
                        response_status=status_code,
                        request_headers=_sanitize_headers(dict(request.headers)),
                    )
                    await db.commit()
                except Exception:
                    await db.rollback()

                return response
            finally:
                if db is not None:
                    await db.close()

        return audit_wrapper
