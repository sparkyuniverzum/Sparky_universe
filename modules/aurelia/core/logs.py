from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from typing import Any, Dict, List

try:  # Optional if running without DB.
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None

_MEMORY: List[Dict[str, Any]] = []
_SCHEMA_READY = False
MAX_MEMORY_LOGS = 500


def _dsn() -> str | None:
    return (
        os.getenv("SPARKY_AURELIA_DSN")
        or os.getenv("SPARKY_DB_DSN")
        or os.getenv("DATABASE_URL")
    )


def _db_available() -> bool:
    return bool(_dsn()) and psycopg is not None


def _salt() -> str:
    value = os.getenv("SPARKY_AURELIA_SALT", "").strip()
    return value or "sparky-aurelia"


def _hash_user(value: str | None) -> str | None:
    if not value:
        return None
    raw = f"{_salt()}{value}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _ensure_schema(conn: Any) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sparky_aurelia_logs (
            id UUID PRIMARY KEY,
            user_hash TEXT,
            event_type TEXT NOT NULL,
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_aurelia_logs_user
        ON sparky_aurelia_logs (user_hash);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_aurelia_logs_event
        ON sparky_aurelia_logs (event_type);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_aurelia_logs_created
        ON sparky_aurelia_logs (created_at DESC);
        """
    )
    _SCHEMA_READY = True


def record_event(user_id: str | None, event_type: str, payload: Dict[str, Any]) -> str:
    event_id = str(uuid.uuid4())
    user_hash = _hash_user(user_id)
    event_type = (event_type or "sync").strip().lower() or "sync"

    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            conn.execute(
                """
                INSERT INTO sparky_aurelia_logs (id, user_hash, event_type, payload)
                VALUES (%s, %s, %s, %s);
                """,
                (event_id, user_hash, event_type, json.dumps(payload)),
            )
        return event_id

    _MEMORY.append(
        {
            "id": event_id,
            "user_hash": user_hash,
            "event_type": event_type,
            "payload": payload,
            "created_at": time.time(),
        }
    )
    if len(_MEMORY) > MAX_MEMORY_LOGS:
        del _MEMORY[: len(_MEMORY) - MAX_MEMORY_LOGS]

    return event_id


def log_stats() -> Dict[str, Any]:
    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            total = conn.execute("SELECT COUNT(*) FROM sparky_aurelia_logs;").fetchone()[0]
            distinct = conn.execute(
                "SELECT COUNT(DISTINCT user_hash) FROM sparky_aurelia_logs;"
            ).fetchone()[0]
            last = conn.execute(
                "SELECT MAX(created_at) FROM sparky_aurelia_logs;"
            ).fetchone()[0]
        return {
            "total": int(total or 0),
            "distinct_users": int(distinct or 0),
            "last_event_at": last,
            "source": "db",
        }

    last = max((item.get("created_at") for item in _MEMORY), default=None)
    users = {item.get("user_hash") for item in _MEMORY if item.get("user_hash")}
    return {
        "total": len(_MEMORY),
        "distinct_users": len(users),
        "last_event_at": last,
        "source": "memory",
    }


def list_events(
    *,
    limit: int = 100,
    user_hash: str | None = None,
    event_type: str | None = None,
) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 200))
    user_hash = user_hash or None
    event_type = event_type or None

    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            rows = conn.execute(
                """
                SELECT id, user_hash, event_type, payload, created_at
                FROM sparky_aurelia_logs
                WHERE (%s IS NULL OR user_hash = %s)
                  AND (%s IS NULL OR event_type = %s)
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (user_hash, user_hash, event_type, event_type, limit),
            ).fetchall()
        logs: List[Dict[str, Any]] = []
        for row in rows:
            payload = row[3]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"raw": payload}
            logs.append(
                {
                    "id": str(row[0]),
                    "user_hash": row[1],
                    "event_type": row[2],
                    "payload": payload or {},
                    "created_at": row[4],
                }
            )
        return logs

    logs = [
        item
        for item in _MEMORY
        if (not user_hash or item.get("user_hash") == user_hash)
        and (not event_type or item.get("event_type") == event_type)
    ]
    logs.sort(key=lambda item: item.get("created_at") or 0, reverse=True)
    return logs[:limit]
