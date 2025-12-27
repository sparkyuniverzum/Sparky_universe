from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple


MAX_ITEMS = 5000


def _parse_decimal(value: str) -> Tuple[Decimal | None, str | None]:
    compact = value.replace(" ", "")
    if "," in compact and "." in compact:
        last_comma = compact.rfind(",")
        last_dot = compact.rfind(".")
        if last_comma > last_dot:
            compact = compact.replace(".", "")
            compact = compact.replace(",", ".")
        else:
            compact = compact.replace(",", "")
    elif "," in compact:
        compact = compact.replace(",", ".")

    try:
        return Decimal(compact), None
    except (InvalidOperation, ValueError):
        return None, "Invalid number format."


def _split_values(raw: str) -> List[str]:
    normalized = raw.replace(";", ",")
    normalized = normalized.replace("\n", ",")
    normalized = normalized.replace("\t", ",")
    parts = [part.strip() for part in normalized.split(",")]
    return [part for part in parts if part]


def _median(values: List[Decimal]) -> Decimal:
    sorted_values = sorted(values)
    count = len(sorted_values)
    midpoint = count // 2
    if count % 2 == 1:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / Decimal("2")


def analyze_sequence(raw: Any) -> Tuple[Dict[str, Any] | None, str | None]:
    if raw is None:
        return None, "Values are required."
    raw_text = str(raw).strip()
    if not raw_text:
        return None, "Values are required."

    items = _split_values(raw_text)
    if not items:
        return None, "No numbers provided."
    if len(items) > MAX_ITEMS:
        return None, f"Too many items (limit {MAX_ITEMS})."

    values: List[Decimal] = []
    for item in items:
        parsed, error = _parse_decimal(item)
        if error or parsed is None:
            return None, f"Invalid number: {item}"
        values.append(parsed)

    count = len(values)
    total = sum(values)
    minimum = min(values)
    maximum = max(values)
    average = total / Decimal(count)
    median = _median(values)

    return {
        "count": count,
        "sum": str(total),
        "min": str(minimum),
        "max": str(maximum),
        "average": str(average),
        "median": str(median),
    }, None
