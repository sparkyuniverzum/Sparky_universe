from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

DATE_FORMATS = {
    "YYYYMMDD": "%Y%m%d",
    "YYMMDD": "%y%m%d",
    "YYYY-MM-DD": "%Y-%m-%d",
    "NONE": "",
}


def _clean_token(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().upper().replace(" ", "")


def _date_label(format_key: str) -> str:
    pattern = DATE_FORMATS.get(format_key, DATE_FORMATS["YYYYMMDD"])
    if not pattern:
        return ""
    return datetime.now(timezone.utc).strftime(pattern)


def generate_batch_labels(
    *,
    prefix: str | None,
    count: int,
    start: int,
    width: int,
    date_format: str,
    separator: str,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if count <= 0 or count > 5000:
        return None, "Count must be between 1 and 5000."
    if width < 1 or width > 12:
        return None, "Width must be between 1 and 12."

    prefix_token = _clean_token(prefix) or "LOT"
    date_label = _date_label(date_format)

    labels: List[str] = []
    for idx in range(count):
        number = str(start + idx).zfill(width)
        parts = [prefix_token]
        if date_label:
            parts.append(date_label)
        parts.append(number)
        labels.append(separator.join(parts))

    return {
        "count": len(labels),
        "prefix": prefix_token,
        "date": date_label,
        "start": start,
        "width": width,
        "separator": separator,
        "labels": labels,
    }, None
