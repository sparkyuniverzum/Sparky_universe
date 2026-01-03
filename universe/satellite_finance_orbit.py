from __future__ import annotations

import json
import os
import re
import time
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, Tuple
from urllib.request import Request, urlopen

try:  # Optional if running without DB yet.
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


SATELLITE_ID = "sparky-finance-orbit-cz"
SOURCE = "cnb.cz"
PERIOD = "daily"
EXCHANGE_CODES = ["EUR", "USD", "GBP", "PLN", "CHF"]
DEFAULT_EXCHANGE_URL = (
    "https://www.cnb.cz/en/financial_markets/foreign_exchange_market/"
    "exchange_rate_fixing/daily.txt"
)

_SCHEMA_READY = False
_LAST_RUN: Dict[str, Any] = {"ts": 0.0, "ok": None, "detail": ""}

DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")


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


def _fetch_text(url: str, timeout: int = 12) -> str:
    req = Request(url, headers={"User-Agent": "SparkyFinanceOrbit/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _parse_decimal(value: str) -> Decimal | None:
    raw = value.strip().replace(" ", "")
    if not raw:
        return None
    if "," in raw and "." in raw:
        last_comma = raw.rfind(",")
        last_dot = raw.rfind(".")
        if last_comma > last_dot:
            raw = raw.replace(".", "")
            raw = raw.replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def _parse_cnb_date(value: str) -> str | None:
    match = DATE_RE.search(value)
    if not match:
        return None
    day, month, year = match.groups()
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def _parse_iso_date(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return _parse_cnb_date(raw)


def _parse_daily_rates(text: str) -> Tuple[Dict[str, Decimal], str | None, str | None]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return {}, None, "Invalid CNB daily rates response."
    rate_date = _parse_cnb_date(lines[0])
    rates: Dict[str, Decimal] = {}
    for line in lines[2:]:
        parts = [item.strip() for item in line.split("|")]
        if len(parts) < 5:
            continue
        code = parts[3]
        if code not in EXCHANGE_CODES:
            continue
        amount = _parse_decimal(parts[2]) or Decimal("1")
        rate = _parse_decimal(parts[4])
        if rate is None or amount == 0:
            continue
        rates[code] = rate / amount
    if not rates:
        return {}, rate_date, "No exchange rates found for target currencies."
    return rates, rate_date, None


def _walk_json(obj: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk_json(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_json(item)


def _extract_repo_record(payload: Any) -> Dict[str, Any] | None:
    for record in _walk_json(payload):
        keys = {str(key).lower() for key in record.keys()}
        if "repo" in " ".join(keys) or record.get("key") == "REPO_RATE":
            return record
    for record in _walk_json(payload):
        keys = {str(key).lower() for key in record.keys()}
        if {"rate", "value"} & keys:
            return record
    return None


def _parse_repo_rate_json(raw: str) -> Tuple[Decimal, str | None, str | None] | None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    record = _extract_repo_record(payload)
    if not record:
        return None
    value = (
        record.get("repo_rate")
        or record.get("repoRate")
        or record.get("rate")
        or record.get("value")
    )
    rate_dec = _parse_decimal(str(value)) if value is not None else None
    if rate_dec is None:
        return None
    valid_from = _parse_iso_date(
        record.get("valid_from")
        or record.get("validFrom")
        or record.get("from")
        or record.get("start")
        or record.get("start_date")
        or record.get("date")
    )
    valid_to = _parse_iso_date(
        record.get("valid_to")
        or record.get("validTo")
        or record.get("to")
        or record.get("end")
        or record.get("end_date")
    )
    return rate_dec, valid_from, valid_to


def _parse_repo_rate_csv(raw: str) -> Tuple[Decimal, str | None, str | None] | None:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    delimiter = ";" if ";" in lines[0] else ","
    header = [item.strip().lower() for item in lines[0].split(delimiter)]
    values = [item.strip() for item in lines[1].split(delimiter)]
    if len(values) != len(header):
        return None
    row = dict(zip(header, values))
    value = row.get("repo_rate") or row.get("rate") or row.get("value")
    rate_dec = _parse_decimal(str(value)) if value is not None else None
    if rate_dec is None:
        return None
    valid_from = _parse_iso_date(
        row.get("valid_from") or row.get("from") or row.get("date")
    )
    valid_to = _parse_iso_date(row.get("valid_to") or row.get("to"))
    return rate_dec, valid_from, valid_to


def _fetch_repo_rate() -> Tuple[Decimal, str | None, str | None] | None:
    url = os.getenv("SPARKY_CNB_REPO_URL", "").strip()
    if url:
        raw = _fetch_text(url)
        parsed = _parse_repo_rate_json(raw) or _parse_repo_rate_csv(raw)
        if parsed:
            return parsed
        raise ValueError("Unable to parse repo rate response.")

    rate = os.getenv("SPARKY_CNB_REPO_RATE", "").strip()
    valid_from = os.getenv("SPARKY_CNB_REPO_VALID_FROM", "").strip()
    valid_to = os.getenv("SPARKY_CNB_REPO_VALID_TO", "").strip()
    rate_dec = _parse_decimal(rate) if rate else None
    if rate_dec is None:
        return None
    return rate_dec, _parse_iso_date(valid_from), _parse_iso_date(valid_to)


def build_finance_orbit_snapshot() -> Tuple[Dict[str, Any] | None, str | None]:
    exchange_url = os.getenv("SPARKY_CNB_EXCHANGE_URL", DEFAULT_EXCHANGE_URL).strip()
    if not exchange_url:
        return None, "CNB exchange rate URL is not configured."

    try:
        exchange_raw = _fetch_text(exchange_url)
    except Exception as exc:
        return None, f"Exchange rates fetch failed: {exc}"

    rates, rate_date, error = _parse_daily_rates(exchange_raw)
    if error:
        return None, error

    try:
        repo_data = _fetch_repo_rate()
    except Exception as exc:
        return None, f"Repo rate fetch failed: {exc}"

    if not repo_data:
        return None, "Repo rate is not configured."

    repo_rate, valid_from, valid_to = repo_data

    data: list[Dict[str, Any]] = []
    for code in EXCHANGE_CODES:
        value = rates.get(code)
        if value is None:
            continue
        data.append(
            {
                "key": f"{code}_CZK",
                "value": float(value),
                "unit": "CZK",
                "type": "exchange_rate",
            }
        )

    repo_entry: Dict[str, Any] = {
        "key": "REPO_RATE",
        "value": float(repo_rate),
        "unit": "%",
        "type": "interest_rate",
    }
    if valid_from:
        repo_entry["valid_from"] = valid_from
    if valid_to:
        repo_entry["valid_to"] = valid_to
    data.append(repo_entry)

    collected_at = rate_date or date.today().isoformat()
    payload = {
        "satellite": SATELLITE_ID,
        "source": SOURCE,
        "collected_at": collected_at,
        "period": PERIOD,
        "data": data,
    }
    return payload, None


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


def run_finance_orbit() -> Tuple[Dict[str, Any] | None, str | None]:
    if not _db_available():
        detail = "DB not configured"
        _LAST_RUN.update({"ts": time.time(), "ok": False, "detail": detail})
        return None, detail

    payload, error = build_finance_orbit_snapshot()
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


def fetch_latest_snapshot() -> Tuple[Dict[str, Any] | None, str | None]:
    dsn = _dsn()
    if not dsn or psycopg is None:
        return None, "DB not configured"
    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            _ensure_schema(conn)
            row = conn.execute(
                """
                SELECT payload
                FROM sparky_satellite_snapshots
                WHERE satellite = %s
                ORDER BY collected_at DESC
                LIMIT 1;
                """,
                (SATELLITE_ID,),
            ).fetchone()
        if not row:
            return None, "No snapshots stored yet."
        payload = row[0]
        if isinstance(payload, str):
            return json.loads(payload), None
        return payload, None
    except Exception as exc:
        return None, f"DB read failed: {exc}"


def last_finance_orbit_run() -> Dict[str, Any]:
    return dict(_LAST_RUN)
