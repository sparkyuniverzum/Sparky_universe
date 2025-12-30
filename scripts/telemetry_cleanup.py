#!/usr/bin/env python3
from __future__ import annotations

import os
import sys


def _dsn() -> str | None:
    return os.getenv("SPARKY_DB_DSN") or os.getenv("DATABASE_URL")


def main() -> None:
    dsn = _dsn()
    if not dsn:
        raise SystemExit("Missing SPARKY_DB_DSN or DATABASE_URL.")

    retention_days = int(os.getenv("SPARKY_TELEMETRY_RETENTION_DAYS", "90"))
    if retention_days <= 0:
        raise SystemExit("Retention days must be greater than zero.")

    try:
        import psycopg
    except Exception as exc:  # pragma: no cover - optional dependency
        raise SystemExit("psycopg is required to run cleanup.") from exc

    query = """
    DELETE FROM telemetry_events
    WHERE ts < now() - (%s * interval '1 day');
    """

    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (retention_days,))
            print(f"Deleted {cur.rowcount} telemetry events.")


if __name__ == "__main__":
    main()
