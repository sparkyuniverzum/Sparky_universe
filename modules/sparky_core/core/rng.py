from __future__ import annotations

import random
from typing import Any, Tuple


def parse_seed(value: Any) -> Tuple[int | None, str | None]:
    if value is None:
        return None, None
    raw = str(value).strip()
    if not raw:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, "Seed must be a whole number."


def make_rng(seed: int | None) -> random.Random:
    if seed is None:
        return random.SystemRandom()
    return random.Random(seed)
