from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple
from urllib.request import Request, urlopen

try:  # Optional if running without DB yet.
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


SATELLITE_ID = "sparky-bavaria-holiday-orbit"
SOURCE = "date.nager.at"
PERIOD = "yearly"

COUNTRY_CZ = "CZ"
COUNTRY_DE = "DE"
REGION_BAVARIA = "DE-BY"

DEFAULT_API_URL = "https://date.nager.at/api/v3/PublicHolidays/{year}/{country}"

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
    req = Request(url, headers={"User-Agent": "SparkyHolidayOrbit/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return json.loads(resp.read().decode(charset, errors="replace"))


def _build_url(year: int, country: str) -> str:
    override = os.getenv("SPARKY_HOLIDAY_API_URL", "").strip()
    template = override or DEFAULT_API_URL
    return template.format(year=year, country=country)


def _normalize_entry(entry: Dict[str, Any], country: str, region: str) -> Dict[str, Any]:
    date_value = str(entry.get("date", "")).strip()
    name = str(entry.get("name", "")).strip()
    local_name = str(entry.get("localName", "")).strip()
    holiday_type = str(entry.get("type", "")).strip().lower() or "public"
    key_label = local_name or name or date_value
    return {
        "key": f"{date_value}:{country}:{key_label}",
        "date": date_value,
        "name": name or local_name,
        "local_name": local_name or name,
        "country": country,
        "region": region,
        "type": "public_holiday",
        "holiday_type": holiday_type,
    }


def _entries_for_country(payload: List[Dict[str, Any]], country: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        if country == COUNTRY_DE:
            counties = entry.get("counties") or []
            applies_to_bavaria = not counties or REGION_BAVARIA in counties
            if not applies_to_bavaria:
                continue
            region = REGION_BAVARIA
        else:
            region = country
        entries.append(_normalize_entry(entry, country, region))
    return entries


def _fetch_holidays(year: int) -> Tuple[List[Dict[str, Any]], str | None]:
    try:
        cz_payload = _fetch_json(_build_url(year, COUNTRY_CZ))
        de_payload = _fetch_json(_build_url(year, COUNTRY_DE))
    except Exception as exc:
        return [], f"Holiday fetch failed: {exc}"
    if not isinstance(cz_payload, list) or not isinstance(de_payload, list):
        return [], "Holiday response format is invalid."

    entries = _entries_for_country(cz_payload, COUNTRY_CZ)
    entries.extend(_entries_for_country(de_payload, COUNTRY_DE))
    return entries, None


def _mark_overlap(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    entries_list = list(entries)
    cz_dates = {entry.get("date") for entry in entries_list if entry.get("country") == COUNTRY_CZ}
    de_dates = {entry.get("date") for entry in entries_list if entry.get("country") == COUNTRY_DE}
    overlap_dates = cz_dates & de_dates
    for entry in entries_list:
        entry["overlap"] = entry.get("date") in overlap_dates
    return entries_list


def build_bavaria_holiday_snapshot() -> Tuple[Dict[str, Any] | None, str | None]:
    today = date.today()
    years = [today.year, today.year + 1]
    all_entries: List[Dict[str, Any]] = []
    for year in years:
        entries, error = _fetch_holidays(year)
        if error:
            return None, error
        all_entries.extend(entries)

    if not all_entries:
        return None, "No holiday data returned."

    deduped: Dict[str, Dict[str, Any]] = {}
    for entry in all_entries:
        deduped[entry["key"]] = entry

    merged = _mark_overlap(deduped.values())
    merged.sort(key=lambda item: (item.get("date", ""), item.get("country", "")))

    payload = {
        "satellite": SATELLITE_ID,
        "source": SOURCE,
        "collected_at": datetime.now(timezone.utc).date().isoformat(),
        "period": PERIOD,
        "data": merged,
        "meta": {
            "regions": [COUNTRY_CZ, REGION_BAVARIA],
            "years": years,
        },
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


def run_bavaria_holiday_orbit() -> Tuple[Dict[str, Any] | None, str | None]:
    if not _db_available():
        detail = "DB not configured"
        _LAST_RUN.update({"ts": time.time(), "ok": False, "detail": detail})
        return None, detail

    payload, error = build_bavaria_holiday_snapshot()
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
    max_age_days: int = 7,
) -> Tuple[Dict[str, Any] | None, str | None]:
    payload, collected_at, error = fetch_latest_snapshot()
    if payload and collected_at:
        now = datetime.now(timezone.utc)
        age_days = (now - collected_at).days
        if age_days <= max_age_days:
            return payload, None

    refresh_payload, refresh_error = run_bavaria_holiday_orbit()
    if refresh_payload:
        return refresh_payload, None
    if payload:
        return payload, refresh_error
    return None, refresh_error or error
