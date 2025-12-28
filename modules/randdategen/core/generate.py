from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Tuple

from modules.sparky_core.core.rng import make_rng, parse_seed

MAX_COUNT = 500


def _parse_date(value: Any, label: str) -> Tuple[date | None, str | None]:
    if value is None:
        return None, f"{label} is required."
    raw = str(value).strip()
    if not raw:
        return None, f"{label} is required."
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date(), None
    except ValueError:
        return None, f"{label} must be YYYY-MM-DD."


def _parse_int(value: Any, *, label: str, default: int | None = None) -> Tuple[int | None, str | None]:
    if value is None or str(value).strip() == "":
        if default is None:
            return None, f"{label} is required."
        return default, None
    raw = str(value).strip()
    try:
        number = int(raw)
    except ValueError:
        return None, f"{label} must be a whole number."
    return number, None


def generate_dates(
    start: Any,
    end: Any,
    count: Any,
    *,
    unique: bool = False,
    seed: Any = None,
) -> Tuple[Dict[str, List[str]] | None, str | None]:
    start_date, error = _parse_date(start, "Start date")
    if error or start_date is None:
        return None, error

    end_date, error = _parse_date(end, "End date")
    if error or end_date is None:
        return None, error

    if start_date > end_date:
        return None, "Start date must be before end date."

    count_int, error = _parse_int(count, label="Count", default=10)
    if error or count_int is None:
        return None, error

    if count_int <= 0 or count_int > MAX_COUNT:
        return None, f"Count must be between 1 and {MAX_COUNT}."

    delta_days = (end_date - start_date).days
    total_days = delta_days + 1

    if unique and count_int > total_days:
        return None, "Count exceeds available unique dates."

    seed_int, error = parse_seed(seed)
    if error:
        return None, error
    rng = make_rng(seed_int)
    values: List[str] = []

    if unique:
        offsets = rng.sample(range(total_days), count_int)
        offsets.sort()
        values = [(start_date + timedelta(days=offset)).isoformat() for offset in offsets]
    else:
        for _ in range(count_int):
            offset = rng.randint(0, delta_days)
            values.append((start_date + timedelta(days=offset)).isoformat())

    return {
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "count": count_int,
        "seed": seed_int,
        "values": values,
    }, None
