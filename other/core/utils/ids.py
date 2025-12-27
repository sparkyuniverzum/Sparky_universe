from __future__ import annotations
import os
import time


def uuid7() -> str:
    """Minimalistická implementace UUIDv7 → canonical string."""
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
        b[i] = rnd[i - 5]  # fill remaining bytes
    hexs = b.hex()
    return f"{hexs[0:8]}-{hexs[8:12]}-{hexs[12:16]}-{hexs[16:20]}-{hexs[20:32]}"


__all__ = ["uuid7"]
