from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple

MAX_COUNT = 2000


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


def generate_numbers(
    min_value: Any,
    max_value: Any,
    count: Any,
    *,
    unique: bool = False,
    sort_result: bool = False,
) -> Tuple[Dict[str, List[int]] | None, str | None]:
    min_int, error = _parse_int(min_value, label="Min", default=1)
    if error or min_int is None:
        return None, error

    max_int, error = _parse_int(max_value, label="Max", default=100)
    if error or max_int is None:
        return None, error

    count_int, error = _parse_int(count, label="Count", default=10)
    if error or count_int is None:
        return None, error

    if min_int > max_int:
        return None, "Min must be less than or equal to max."
    if count_int <= 0 or count_int > MAX_COUNT:
        return None, f"Count must be between 1 and {MAX_COUNT}."

    rng = random.SystemRandom()
    if unique:
        range_size = max_int - min_int + 1
        if count_int > range_size:
            return None, "Count exceeds available unique values."
        values = rng.sample(range(min_int, max_int + 1), count_int)
    else:
        values = [rng.randint(min_int, max_int) for _ in range(count_int)]

    if sort_result:
        values.sort()

    return {
        "min": min_int,
        "max": max_int,
        "count": count_int,
        "values": values,
    }, None
