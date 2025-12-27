# app/core/idempotency.py
# backend/app/core/idempotency.py
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional, Callable, Awaitable, Tuple

from fastapi import Header, Request, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.idempotency.model import IdempotencyLog
from app.core.db.database import get_session  # tvá původní dependency
from fastapi.encoders import jsonable_encoder


def _json_dumps(obj: Any) -> str:
    """Bezpečné JSON dumpování – při chybě raději vracíme '{}'."""
    try:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return "{}"


def _actor_identity(request: Request) -> str:
    """Identify caller (user id or X-Actor-Id) to scope idempotency reuse."""
    actor = request.headers.get("x-actor-id") or ""
    user = getattr(request.state, "user", None)
    if user and getattr(user, "id", None):
        actor = str(user.id)
    return actor


def _hash_payload(raw: str, actor: str | None = None) -> str:
    """
    Hash payload together s identitou volajícího, aby klíč nebyl sdílitelný napříč uživateli.
    Actor se přidává jen při výpočtu, uložený hash zůstává jedinou hodnotou.
    """
    prefix = f"{actor or ''}|"
    return hashlib.sha256(f"{prefix}{raw}".encode("utf-8")).hexdigest()


async def idempotent(
    request: Request,
    x_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_session),
    body: Any | None = None,
) -> Optional[JSONResponse]:
    if not x_key:
        return None

    raw = "" if body is None else _json_dumps(body)
    actor = _actor_identity(request)
    payload_hash = _hash_payload(raw, actor)

    request.state.request_body = raw
    request.state.payload_hash = payload_hash
    request.state.idem_actor = actor

    row = (
        await db.execute(select(IdempotencyLog).where(IdempotencyLog.key == x_key))
    ).scalar_one_or_none()

    # ✅ HIT: kontrolujeme shodu metody, path i payload hash (včetně actor)
    if row and row.response_code is not None:
        legacy_hash = _hash_payload(raw, None)
        payload_match = row.payload_hash in {payload_hash, legacy_hash}
        path_match = row.path == str(request.url.path)
        method_match = row.method == request.method
        if payload_match and path_match and method_match:
            try:
                data = json.loads(row.response_body or "{}")
            except Exception:
                data = {}
            print(
                f"[IDEMPOTENCY] HIT key={x_key} method={request.method} "
                f"path={request.url.path} status={row.response_code}"
            )
            return JSONResponse(status_code=int(row.response_code), content=data)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Idempotency conflict: key already used with different request"},
        )

    print(
        f"[IDEMPOTENCY] MISS key={x_key} method={request.method} "
        f"path={request.url.path}"
    )
    return None


async def idempotent_upsert_response(
    request: Request,
    status_code: int,
    body: Any,
    db: AsyncSession,
    x_key: str,
) -> None:
    """
    Uloží/aktualizuje idempotentní odpověď do tabulky idempotency_logs
    a zajistí commit, aby byl záznam viditelný pro další request.
    """
    req_body: str = getattr(request.state, "request_body", "")
    payload_hash: Optional[str] = getattr(request.state, "payload_hash", None)

    existing = (
        await db.execute(select(IdempotencyLog).where(IdempotencyLog.key == x_key))
    ).scalar_one_or_none()

    # 🔑 Tady je ten zásadní rozdíl – tělo převádíme na JSON-safe strukturu
    safe_body = jsonable_encoder(body)

    if existing is None:
        stmt = insert(IdempotencyLog).values(
            key=x_key,
            method=request.method,
            path=str(request.url.path),
            payload_hash=payload_hash,
            response_code=int(status_code),
            response_body=_json_dumps(safe_body),
        )
        await db.execute(stmt)
        print(f"[IDEMPOTENCY] UPSERT: INSERT key={x_key} status={status_code}")
    else:
        stmt = (
            update(IdempotencyLog)
            .where(IdempotencyLog.key == existing.key)
            .values(
                response_code=int(status_code),
                response_body=_json_dumps(safe_body),
                payload_hash=payload_hash or existing.payload_hash,
            )
        )
        await db.execute(stmt)
        print(f"[IDEMPOTENCY] UPSERT: UPDATE key={x_key} status={status_code}")

    await db.commit()


# ─────────────────────────────────────────────────────────────────────
# 🔧 NOVÝ HELPER: execute_idempotent – používají routery (products atd.)
# ─────────────────────────────────────────────────────────────────────
async def execute_idempotent(
    *,
    request: Request,
    db: AsyncSession,
    idempotency_key: Optional[str],
    handler: Callable[[], Awaitable[Tuple[int, dict]]],
    body: Any | None = None,
) -> Tuple[int, dict]:
    if not idempotency_key:
        return await handler()

    raw = "" if body is None else _json_dumps(body)
    actor = _actor_identity(request)
    payload_hash = _hash_payload(raw, actor)

    # pro upsert
    request.state.request_body = raw
    request.state.payload_hash = payload_hash
    request.state.idem_actor = actor

    row = (
        await db.execute(
            select(IdempotencyLog).where(IdempotencyLog.key == idempotency_key)
        )
    ).scalar_one_or_none()

    # ✅ jen podle klíče + shoda metody/path/hash
    if row and row.response_code is not None:
        legacy_hash = _hash_payload(raw, None)
        payload_match = row.payload_hash in {payload_hash, legacy_hash}
        path_match = row.path == str(request.url.path)
        method_match = row.method == request.method
        if payload_match and path_match and method_match:
            try:
                data = json.loads(row.response_body or "{}")
            except Exception:
                data = {}
            print(
                f"[IDEMPOTENCY] HIT key={idempotency_key} method={request.method} "
                f"path={request.url.path} status={row.response_code}"
            )
            return (int(row.response_code), data)
        return (
            status.HTTP_409_CONFLICT,
            {"detail": "Idempotency conflict: key already used with different request"},
        )

    print(
        f"[IDEMPOTENCY] MISS key={idempotency_key} method={request.method} "
        f"path={request.url.path}"
    )

    status_code, result = await handler()
    await idempotent_upsert_response(
        request=request,
        status_code=status_code,
        body=result,
        db=db,
        x_key=idempotency_key,
    )
    return (status_code, result)
