from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple


MAX_ITEMS = 1000


def _normalize_number(value: str) -> str:
    compact = value.strip().replace(" ", "")
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
    return compact


def _parse_decimal_list(raw: object) -> Tuple[List[Decimal] | None, str | None]:
    if raw is None:
        return None, "Numbers are required."
    text = str(raw).strip()
    if not text:
        return None, "Numbers are required."

    tokens = [token for token in re.split(r"[,\s]+", text) if token]
    if not tokens:
        return None, "Numbers are required."
    if len(tokens) > MAX_ITEMS:
        return None, f"Too many numbers (limit {MAX_ITEMS})."

    values: List[Decimal] = []
    for token in tokens:
        normalized = _normalize_number(token)
        try:
            values.append(Decimal(normalized))
        except (InvalidOperation, ValueError):
            return None, f"Invalid number: {token}"
    return values, None


def _median(values: List[Decimal]) -> Decimal:
    count = len(values)
    mid = count // 2
    if count % 2 == 1:
        return values[mid]
    return (values[mid - 1] + values[mid]) / Decimal(2)


def summarize_stats(raw: object) -> Tuple[Dict[str, object] | None, str | None]:
    values, error = _parse_decimal_list(raw)
    if error or values is None:
        return None, error

    values.sort()
    count = len(values)
    total = sum(values, Decimal(0))
    mean = total / Decimal(count)
    median = _median(values)

    if count == 1:
        q1 = values[0]
        q3 = values[0]
    else:
        mid = count // 2
        lower = values[:mid]
        upper = values[mid:] if count % 2 == 0 else values[mid + 1 :]
        q1 = _median(lower)
        q3 = _median(upper)

    variance_pop = sum((value - mean) ** 2 for value in values) / Decimal(count)
    stdev_pop = variance_pop.sqrt()

    if count > 1:
        variance_sample = sum((value - mean) ** 2 for value in values) / Decimal(
            count - 1
        )
        stdev_sample = variance_sample.sqrt()
    else:
        variance_sample = None
        stdev_sample = None

    freq: Dict[Decimal, int] = {}
    for value in values:
        freq[value] = freq.get(value, 0) + 1
    max_count = max(freq.values())
    if max_count == 1:
        modes: List[Decimal] = []
    else:
        modes = [value for value, count in freq.items() if count == max_count]
        modes.sort()

    return {
        "count": count,
        "sum": str(total),
        "min": str(values[0]),
        "max": str(values[-1]),
        "mean": str(mean),
        "median": str(median),
        "q1": str(q1),
        "q3": str(q3),
        "variance_pop": str(variance_pop),
        "stdev_pop": str(stdev_pop),
        "variance_sample": str(variance_sample) if variance_sample is not None else None,
        "stdev_sample": str(stdev_sample) if stdev_sample is not None else None,
        "modes": [str(value) for value in modes],
    }, None
