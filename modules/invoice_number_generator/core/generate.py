from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _year_label(year: int | None) -> int:
    if year and 2000 <= year <= 2100:
        return year
    return datetime.now(timezone.utc).year


def generate_invoice_numbers(
    *,
    prefix: str | None,
    year: int | None,
    start: int,
    count: int,
    width: int,
    separator: str,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if count <= 0 or count > 5000:
        return None, "Count must be between 1 and 5000."
    if width < 1 or width > 12:
        return None, "Width must be between 1 and 12."
    if start < 0:
        return None, "Start must be zero or higher."

    prefix_token = (prefix or "INV").strip().upper().replace(" ", "")
    year_value = _year_label(year)

    numbers: List[str] = []
    for idx in range(count):
        number = str(start + idx).zfill(width)
        parts = [prefix_token, str(year_value), number]
        numbers.append(separator.join(parts))

    return {
        "count": len(numbers),
        "prefix": prefix_token,
        "year": year_value,
        "start": start,
        "width": width,
        "separator": separator,
        "numbers": numbers,
    }, None
