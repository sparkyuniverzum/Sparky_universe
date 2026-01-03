from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:  # Optional if running without DB yet.
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


SATELLITE_ID = "sparky-crypto-orbit"
SOURCE = "coingecko.com"
PERIOD = "hourly"
VS_CURRENCY = "usd"
COIN_IDS = [
    "bitcoin",
    "ethereum",
    "solana",
    "binancecoin",
    "ripple",
    "cardano",
    "dogecoin",
    "polkadot",
    "avalanche-2",
    "chainlink",
]
DEFAULT_MARKET_URL = "https://api.coingecko.com/api/v3/coins/markets"

_SCHEMA_READY = False
_LAST_RUN: Dict[str, Any] = {"ts": 0.0, "ok": None, "detail": ""}


def _dsn() -> str | None:
    return (
        os.getenv("SPARKY_SATELLITE_DB_DSN")
        or os.getenv("SPARKY_ADMIN_DB_DSN")
        or os.getenv("SPARKY_DB_DSN")
        or os.getenv("DATABASE_URL")
    )


def _db_available() -> bool:
    return bool(_dsn()) and psycopg is not None


def _ensure_schema(conn: Any) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sparky_satellite_snapshots (
            id BIGSERIAL PRIMARY KEY,
            satellite TEXT NOT NULL,
            source TEXT NOT NULL,
            period TEXT NOT NULL,
            collected_at TIMESTAMPTZ NOT NULL,
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sparky_satellite_latest
        ON sparky_satellite_snapshots (satellite, collected_at DESC);
        """
    )
    _SCHEMA_READY = True


def _fetch_json(url: str, timeout: int = 12) -> Any:
    req = Request(url, headers={"User-Agent": "SparkyCryptoOrbit/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return json.loads(resp.read().decode(charset, errors="replace"))


def _build_market_url() -> str:
    query = urlencode(
        {
            "vs_currency": VS_CURRENCY,
            "ids": ",".join(COIN_IDS),
            "order": "market_cap_desc",
            "per_page": str(len(COIN_IDS)),
            "page": "1",
            "sparkline": "false",
            "price_change_percentage": "24h",
        }
    )
    return f"{DEFAULT_MARKET_URL}?{query}"


def _collected_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def build_crypto_orbit_snapshot() -> Tuple[Dict[str, Any] | None, str | None]:
    url = os.getenv("SPARKY_COINGECKO_URL", "").strip() or _build_market_url()
    if not url:
        return None, "CoinGecko URL is not configured."

    try:
        payload = _fetch_json(url)
    except Exception as exc:
        return None, f"CoinGecko fetch failed: {exc}"

    if not isinstance(payload, list):
        return None, "CoinGecko response format is invalid."

    data: list[Dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        coin_id = str(item.get("id", "")).strip()
        if not coin_id:
            continue
        if coin_id not in COIN_IDS:
            continue
        data.append(
            {
                "key": coin_id,
                "symbol": str(item.get("symbol", "")).upper(),
                "rank": item.get("market_cap_rank"),
                "price": item.get("current_price"),
                "market_cap": item.get("market_cap"),
                "volume_24h": item.get("total_volume"),
                "change_24h_pct": item.get("price_change_percentage_24h"),
                "type": "crypto_quote",
            }
        )

    if not data:
        return None, "No crypto data returned from CoinGecko."

    snapshot = {
        "satellite": SATELLITE_ID,
        "source": SOURCE,
        "collected_at": _collected_at(),
        "period": PERIOD,
        "currency": VS_CURRENCY,
        "data": data,
    }
    return snapshot, None


def store_snapshot(payload: Dict[str, Any]) -> None:
    dsn = _dsn()
    if not dsn or psycopg is None:
        raise RuntimeError("DB not configured")
    with psycopg.connect(dsn, autocommit=True) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO sparky_satellite_snapshots (
                satellite, source, period, collected_at, payload
            ) VALUES (%s, %s, %s, now(), %s::jsonb);
            """,
            (
                payload.get("satellite"),
                payload.get("source"),
                payload.get("period"),
                json.dumps(payload),
            ),
        )


def run_crypto_orbit() -> Tuple[Dict[str, Any] | None, str | None]:
    if not _db_available():
        detail = "DB not configured"
        _LAST_RUN.update({"ts": time.time(), "ok": False, "detail": detail})
        return None, detail

    payload, error = build_crypto_orbit_snapshot()
    if error:
        _LAST_RUN.update({"ts": time.time(), "ok": False, "detail": error})
        return None, error

    try:
        store_snapshot(payload)
    except Exception as exc:
        detail = f"DB write failed: {exc}"
        _LAST_RUN.update({"ts": time.time(), "ok": False, "detail": detail})
        return None, detail

    _LAST_RUN.update({"ts": time.time(), "ok": True, "detail": "Snapshot stored"})
    return payload, None


def fetch_latest_snapshot() -> Tuple[Dict[str, Any] | None, datetime | None, str | None]:
    dsn = _dsn()
    if not dsn or psycopg is None:
        return None, None, "DB not configured"
    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            _ensure_schema(conn)
            row = conn.execute(
                """
                SELECT payload, collected_at
                FROM sparky_satellite_snapshots
                WHERE satellite = %s
                ORDER BY collected_at DESC
                LIMIT 1;
                """,
                (SATELLITE_ID,),
            ).fetchone()
        if not row:
            return None, None, "No snapshots stored yet."
        payload = row[0]
        collected_at = row[1]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return payload, collected_at, None
    except Exception as exc:
        return None, None, f"DB read failed: {exc}"


def ensure_latest_snapshot(
    max_age_seconds: int = 3600,
) -> Tuple[Dict[str, Any] | None, str | None]:
    payload, collected_at, error = fetch_latest_snapshot()
    if payload and collected_at:
        now = datetime.now(timezone.utc)
        age = (now - collected_at).total_seconds()
        if age <= max_age_seconds:
            return payload, None

    refresh_payload, refresh_error = run_crypto_orbit()
    if refresh_payload:
        return refresh_payload, None
    if payload:
        return payload, refresh_error
    return None, refresh_error or error


def refresh_token_valid(token: str | None) -> bool:
    expected = os.getenv("SPARKY_CRYPTO_ORBIT_TOKEN", "").strip()
    if not expected:
        return False
    return token == expected
