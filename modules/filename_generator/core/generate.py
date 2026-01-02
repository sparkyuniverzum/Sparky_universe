from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

DATE_FORMATS = {
    "YYYYMMDD": "%Y%m%d",
    "YYYY-MM-DD": "%Y-%m-%d",
    "YYYY-MM": "%Y-%m",
    "NONE": "",
}


def _clean_token(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().replace(" ", "_")


def _date_label(format_key: str) -> str:
    pattern = DATE_FORMATS.get(format_key, DATE_FORMATS["YYYYMMDD"])
    if not pattern:
        return ""
    return datetime.now(timezone.utc).strftime(pattern)


def generate_filenames(
    *,
    prefix: str | None,
    extension: str | None,
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

    prefix_token = _clean_token(prefix) or "file"
    ext = _clean_token(extension or "txt")
    if ext.startswith("."):
        ext = ext[1:]
    if not ext:
        ext = "txt"

    date_label = _date_label(date_format)

    files: List[str] = []
    for idx in range(count):
        number = str(start + idx).zfill(width)
        parts = [prefix_token]
        if date_label:
            parts.append(date_label)
        parts.append(number)
        name = separator.join(parts)
        files.append(f"{name}.{ext}")

    return {
        "count": len(files),
        "prefix": prefix_token,
        "extension": ext,
        "date": date_label,
        "start": start,
        "width": width,
        "separator": separator,
        "files": files,
    }, None
