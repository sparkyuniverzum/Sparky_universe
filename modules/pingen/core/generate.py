from __future__ import annotations

import secrets
from typing import Any, Dict, List, Tuple

MAX_COUNT = 500
MAX_LENGTH = 12


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


def generate_pins(
    length: Any,
    count: Any,
    *,
    unique: bool = False,
) -> Tuple[Dict[str, List[str]] | None, str | None]:
    length_int, error = _parse_int(length, label="Length", default=4)
    if error or length_int is None:
        return None, error

    count_int, error = _parse_int(count, label="Count", default=10)
    if error or count_int is None:
        return None, error

    if length_int <= 0 or length_int > MAX_LENGTH:
        return None, f"Length must be between 1 and {MAX_LENGTH}."
    if count_int <= 0 or count_int > MAX_COUNT:
        return None, f"Count must be between 1 and {MAX_COUNT}."

    max_unique = 10 ** length_int
    if unique and count_int > max_unique:
        return None, "Count exceeds unique PIN space."

    pins: List[str] = []
    seen = set()
    while len(pins) < count_int:
        pin = "".join(str(secrets.randbelow(10)) for _ in range(length_int))
        if unique and pin in seen:
            continue
        seen.add(pin)
        pins.append(pin)

    return {
        "count": count_int,
        "length": length_int,
        "values": pins,
    }, None
