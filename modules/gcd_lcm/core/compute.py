from __future__ import annotations

import math
import re
from functools import reduce
from typing import Dict, List, Tuple


MAX_ITEMS = 100


def _parse_int_list(raw: object) -> Tuple[List[int] | None, str | None]:
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

    numbers: List[int] = []
    for token in tokens:
        try:
            numbers.append(int(token))
        except ValueError:
            return None, f"Invalid integer: {token}"

    if len(numbers) < 2:
        return None, "Provide at least two numbers."
    return numbers, None


def _lcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // math.gcd(a, b)


def compute_gcd_lcm(raw: object) -> Tuple[Dict[str, object] | None, str | None]:
    numbers, error = _parse_int_list(raw)
    if error or numbers is None:
        return None, error

    abs_numbers = [abs(value) for value in numbers]
    gcd_value = reduce(math.gcd, abs_numbers)
    lcm_value = reduce(_lcm, abs_numbers)

    return {
        "count": len(numbers),
        "numbers": numbers,
        "gcd": gcd_value,
        "lcm": lcm_value,
    }, None
