from __future__ import annotations

import math
from typing import Dict, List, Tuple


def _parse_int(value: object) -> Tuple[int | None, str | None]:
    if value is None:
        return None, "Number is required."
    raw = str(value).strip()
    if not raw:
        return None, "Number is required."
    compact = raw.replace(" ", "")
    try:
        return int(compact), None
    except ValueError:
        return None, "Number must be a whole integer."


def _factorize(value: int) -> List[tuple[int, int]]:
    remaining = value
    factors: List[tuple[int, int]] = []

    count = 0
    while remaining % 2 == 0:
        remaining //= 2
        count += 1
    if count:
        factors.append((2, count))

    divisor = 3
    while divisor * divisor <= remaining:
        count = 0
        while remaining % divisor == 0:
            remaining //= divisor
            count += 1
        if count:
            factors.append((divisor, count))
        divisor += 2

    if remaining > 1:
        factors.append((remaining, 1))
    return factors


def analyze_prime(value: object) -> Tuple[Dict[str, object] | None, str | None]:
    number, error = _parse_int(value)
    if error or number is None:
        return None, error

    abs_value = abs(number)
    if abs_value < 2:
        return None, "Number must be at least 2 in absolute value."

    factors = _factorize(abs_value)
    is_prime = number > 1 and len(factors) == 1 and factors[0][1] == 1

    divisor_count = 1
    factor_labels: List[str] = []
    for prime, exp in factors:
        divisor_count *= exp + 1
        label = f"{prime}^{exp}" if exp > 1 else str(prime)
        factor_labels.append(label)

    factorization_parts = ["-1"] if number < 0 else []
    factorization_parts.extend(factor_labels)

    return {
        "value": str(number),
        "abs_value": str(abs_value),
        "is_prime": bool(is_prime),
        "divisor_count": divisor_count,
        "factors": factor_labels,
        "factorization": " * ".join(factorization_parts),
        "smallest_factor": factors[0][0] if factors else None,
    }, None
