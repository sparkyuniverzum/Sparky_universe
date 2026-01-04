from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:  # Optional if running without DB.
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


_MEMORY: Dict[str, Any] = {
    "raw": {},
    "events": [],
}
_SCHEMA_READY = False


def _dsn() -> str | None:
    return (
        os.getenv("SPARKY_SOLANA_DSN")
        or os.getenv("SPARKY_DB_DSN")
        or os.getenv("DATABASE_URL")
    )


def _db_available() -> bool:
    return bool(_dsn()) and psycopg is not None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_schema(conn: Any) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sparky_solana_raw_events (
            signature TEXT PRIMARY KEY,
            slot BIGINT,
            block_time TIMESTAMPTZ,
            program_ids JSONB,
            accounts JSONB,
            instructions JSONB,
            logs JSONB,
            payload JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sparky_solana_events (
            id BIGSERIAL PRIMARY KEY,
            star TEXT NOT NULL,
            impact_level INTEGER NOT NULL,
            event JSONB NOT NULL,
            source_signature TEXT,
            valid_from TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_solana_events_star_created
        ON sparky_solana_events (star, created_at DESC);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sparky_solana_cursors (
            key TEXT PRIMARY KEY,
            cursor JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    _SCHEMA_READY = True


def record_raw(payload: Dict[str, Any]) -> bool:
    signature = str(payload.get("signature") or "").strip()
    if not signature:
        return False
    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            conn.execute(
                """
                INSERT INTO sparky_solana_raw_events (
                    signature, slot, block_time, program_ids, accounts,
                    instructions, logs, payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (signature) DO NOTHING;
                """,
                (
                    signature,
                    payload.get("slot"),
                    payload.get("block_time"),
                    json.dumps(payload.get("program_ids") or []),
                    json.dumps(payload.get("accounts") or []),
                    json.dumps(payload.get("instructions") or []),
                    json.dumps(payload.get("logs") or []),
                    json.dumps(payload),
                ),
            )
        return True

    if signature in _MEMORY["raw"]:
        return False
    _MEMORY["raw"][signature] = payload
    return True


def record_event(event: Dict[str, Any]) -> None:
    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            conn.execute(
                """
                INSERT INTO sparky_solana_events (
                    star, impact_level, event, source_signature, valid_from
                ) VALUES (%s, %s, %s, %s, %s);
                """,
                (
                    event.get("star"),
                    int(event.get("impact_level", 0)),
                    json.dumps(event),
                    (event.get("source_refs") or [None])[0],
                    event.get("valid_from"),
                ),
            )
        return

    _MEMORY["events"].append(event)


def list_events(star: str, limit: int = 20) -> List[Dict[str, Any]]:
    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            rows = conn.execute(
                """
                SELECT event
                FROM sparky_solana_events
                WHERE star = %s
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (star, limit),
            ).fetchall()
        events: List[Dict[str, Any]] = []
        for row in rows:
            payload = row[0]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"raw": payload}
            events.append(payload)
        return events

    events = [event for event in _MEMORY["events"] if event.get("star") == star]
    events.sort(key=lambda item: item.get("valid_from") or "", reverse=True)
    return events[:limit]


def list_recent_events(star: str, since: datetime) -> List[Dict[str, Any]]:
    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            rows = conn.execute(
                """
                SELECT event
                FROM sparky_solana_events
                WHERE star = %s AND valid_from >= %s
                ORDER BY created_at DESC;
                """,
                (star, since),
            ).fetchall()
        events: List[Dict[str, Any]] = []
        for row in rows:
            payload = row[0]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"raw": payload}
            events.append(payload)
        return events

    events = []
    for event in _MEMORY["events"]:
        if event.get("star") != star:
            continue
        valid_from = event.get("valid_from")
        if isinstance(valid_from, datetime):
            compare = valid_from
        else:
            try:
                compare = datetime.fromisoformat(str(valid_from))
            except ValueError:
                compare = _utc_now()
        if compare >= since:
            events.append(event)
    events.sort(key=lambda item: item.get("valid_from") or "", reverse=True)
    return events


def get_cursor(key: str) -> Optional[Dict[str, Any]]:
    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            row = conn.execute(
                "SELECT cursor FROM sparky_solana_cursors WHERE key = %s",
                (key,),
            ).fetchone()
        if not row:
            return None
        payload = row[0]
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                return None
        return payload

    return _MEMORY.get("cursor", {}).get(key)


def set_cursor(key: str, cursor: Dict[str, Any]) -> None:
    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            conn.execute(
                """
                INSERT INTO sparky_solana_cursors (key, cursor, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (key)
                DO UPDATE SET cursor = EXCLUDED.cursor, updated_at = now();
                """,
                (key, json.dumps(cursor)),
            )
        return

    memory_cursor = _MEMORY.setdefault("cursor", {})
    memory_cursor[key] = cursor


def raw_count() -> int:
    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            row = conn.execute("SELECT COUNT(*) FROM sparky_solana_raw_events").fetchone()
        return int(row[0]) if row else 0
    return len(_MEMORY["raw"])


def event_count() -> int:
    if _db_available():
        with psycopg.connect(_dsn(), autocommit=True) as conn:
            _ensure_schema(conn)
            row = conn.execute("SELECT COUNT(*) FROM sparky_solana_events").fetchone()
        return int(row[0]) if row else 0
    return len(_MEMORY["events"])


def last_ingest_at() -> Optional[float]:
    cursor = get_cursor("last_ingest")
    if not cursor:
        return None
    try:
        return float(cursor.get("ts", 0.0))
    except (TypeError, ValueError):
        return None


def set_last_ingest_at() -> None:
    set_cursor("last_ingest", {"ts": time.time()})
