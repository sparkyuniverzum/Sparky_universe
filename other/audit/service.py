from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audit.model import AuditLog


def _sanitize(obj: Any) -> Any:
    sensitive_keys = {
        "password",
        "password_hash",
        "access_token",
        "refresh_token",
        "token",
        "authorization",
        "api_key",
        "x-api-key",
        "cookie",
        "cookies",
        "session",
        "set-cookie",
        "authorization",
        "proxy-authorization",
        "x-amz-security-token",
        "x-csrf-token",
    }
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump(mode="json")
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            if str(k).lower() in sensitive_keys:
                clean[k] = "***"
            else:
                clean[k] = _sanitize(v)
        return clean
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def _serialize_payload(payload: Any | None, *, max_len: int = 4000) -> str:
    """Uloží payload jako čitelný text (většinou JSON) s maskováním citlivých polí."""

    payload = _sanitize(payload)
    if payload is None:
        return ""

    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")

    if isinstance(payload, (dict, list)):
        try:
            text = json.dumps(payload, ensure_ascii=False)
            if len(text) > max_len:
                return text[:max_len] + " [truncated]"
            return text
        except TypeError:
            return str(payload)

    text = str(payload)
    if len(text) > max_len:
        return text[:max_len] + " [truncated]"
    return text


async def log_audit(
    db: AsyncSession,
    *,
    actor_id: Optional[str],
    method: str,
    resource: str,
    request_payload: Any,
    response_status: int,
    request_headers: dict[str, str] | None = None,
    client_ip: str | None = None,
) -> AuditLog:
    headers_serialized = _serialize_payload(request_headers, max_len=2000) if request_headers else ""
    entry = AuditLog(
        at=datetime.now(timezone.utc),
        actor_id=actor_id or "anonymous",
        method=method,
        resource=resource,
        request_payload=_serialize_payload(request_payload),
        response_status=response_status if response_status is not None else 0,
        request_headers=headers_serialized,
    )

    db.add(entry)
    return entry


__all__ = ["log_audit"]
