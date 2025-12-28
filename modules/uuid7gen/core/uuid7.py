from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Tuple

MAX_COUNT = 1000


def uuid7() -> str:
    """Minimal UUIDv7 implementation (canonical string)."""
    msec = int(time.time_ns() // 1_000_000)
    if msec >= (1 << 48):
        raise OverflowError("timestamp too large for UUIDv7")

    rnd = bytearray(os.urandom(12))
    b = bytearray(16)
    th = msec >> 16
    tl = msec & 0xFFFF
    b[0] = (th >> 16) & 0xFF
    b[1] = (th >> 8) & 0xFF
    b[2] = th & 0xFF
    b[3] = (tl >> 8) & 0xFF
    b[4] = tl & 0xFF
    b[5] = 0x70 | (rnd[0] & 0x0F)  # version 7
    b[6] = 0x80 | (rnd[1] & 0x3F)  # variant RFC 4122
    for i in range(7, 16):
        b[i] = rnd[i - 5]

    hexs = b.hex()
    return f"{hexs[0:8]}-{hexs[8:12]}-{hexs[12:16]}-{hexs[16:20]}-{hexs[20:32]}"


def _parse_count(value: Any) -> Tuple[int | None, str | None]:
    if value is None:
        return 1, None
    raw = str(value).strip()
    if not raw:
        return 1, None
    try:
        count = int(raw)
    except ValueError:
        return None, "Count must be a whole number."
    if count <= 0:
        return None, "Count must be greater than zero."
    if count > MAX_COUNT:
        return None, f"Count must not exceed {MAX_COUNT}."
    return count, None


def generate_uuid7(count: Any = 1) -> Tuple[Dict[str, List[str]] | None, str | None]:
    count_int, error = _parse_count(count)
    if error or count_int is None:
        return None, error

    values = [uuid7() for _ in range(count_int)]
    return {"count": count_int, "values": values}, None
