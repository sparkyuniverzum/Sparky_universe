from __future__ import annotations

import secrets
import time
from typing import Any, Dict, List, Tuple

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
MAX_COUNT = 1000
TIME_BITS = 48
RANDOM_BITS = 80
TOTAL_LENGTH = 26


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


def _encode_base32(value: int, length: int = TOTAL_LENGTH) -> str:
    chars: List[str] = []
    for _ in range(length):
        chars.append(CROCKFORD[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def _ulid() -> str:
    time_ms = int(time.time_ns() // 1_000_000)
    if time_ms >= (1 << TIME_BITS):
        raise OverflowError("Timestamp too large for ULID")
    random_bits = secrets.randbits(RANDOM_BITS)
    value = (time_ms << RANDOM_BITS) | random_bits
    return _encode_base32(value)


def generate_ulids(
    count: Any,
    *,
    uppercase: bool = True,
) -> Tuple[Dict[str, List[str]] | None, str | None]:
    count_int, error = _parse_int(count, label="Count", default=10)
    if error or count_int is None:
        return None, error

    if count_int <= 0 or count_int > MAX_COUNT:
        return None, f"Count must be between 1 and {MAX_COUNT}."

    try:
        values = [_ulid() for _ in range(count_int)]
    except OverflowError as exc:
        return None, str(exc)

    if not uppercase:
        values = [value.lower() for value in values]

    return {
        "count": count_int,
        "uppercase": bool(uppercase),
        "values": values,
    }, None
