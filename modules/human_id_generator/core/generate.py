from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

DATE_FORMATS = {
    "YYYY-MM-DD": "%Y-%m-%d",
    "YYYYMMDD": "%Y%m%d",
    "YYYY-MM": "%Y-%m",
    "YYYY": "%Y",
    "NONE": "",
}


def _clean_token(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().upper().replace(" ", "")


def _date_label(format_key: str, custom: str | None) -> str:
    if custom and custom.strip():
        return custom.strip()
    pattern = DATE_FORMATS.get(format_key, DATE_FORMATS["YYYY-MM-DD"])
    if not pattern:
        return ""
    return datetime.now(timezone.utc).strftime(pattern)


def generate_ids(
    *,
    prefix: str | None,
    count: int,
    start: int,
    width: int,
    date_format: str,
    custom_date: str | None,
    separator: str,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if count <= 0 or count > 5000:
        return None, "Count must be between 1 and 5000."
    if width < 1 or width > 12:
        return None, "Width must be between 1 and 12."

    prefix_token = _clean_token(prefix) or "ID"
    date_label = _date_label(date_format, custom_date)

    ids: List[str] = []
    for idx in range(count):
        number = str(start + idx).zfill(width)
        parts = [prefix_token]
        if date_label:
            parts.append(date_label)
        parts.append(number)
        ids.append(separator.join(parts))

    return {
        "count": len(ids),
        "prefix": prefix_token,
        "date": date_label,
        "start": start,
        "width": width,
        "separator": separator,
        "ids": ids,
    }, None
