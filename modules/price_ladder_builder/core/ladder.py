from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple


def _parse_decimal(value: str | None) -> Tuple[Decimal | None, str | None]:
    if not value or not value.strip():
        return None, "Enter a price."
    try:
        cleaned = value.strip().replace(" ", "")
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        return Decimal(cleaned), None
    except (InvalidOperation, ValueError):
        return None, "Price must be a number."


def build_ladder(
    min_price: str | None,
    max_price: str | None,
    *,
    steps: int | None = None,
    increment: str | None = None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    min_value, error = _parse_decimal(min_price)
    if error:
        return None, error
    max_value, error = _parse_decimal(max_price)
    if error:
        return None, error
    assert min_value is not None and max_value is not None

    if min_value < 0 or max_value < 0:
        return None, "Prices must be positive."
    if max_value < min_value:
        return None, "Max price must be >= min price."

    increment_value = None
    if increment and increment.strip():
        increment_value, error = _parse_decimal(increment)
        if error:
            return None, error
    if steps is not None and steps < 2 and increment_value is None:
        return None, "Steps must be at least 2."

    prices: List[str] = []
    if steps and steps >= 2:
        step_count = steps
        delta = (max_value - min_value) / Decimal(step_count - 1)
        for idx in range(step_count):
            price = min_value + delta * Decimal(idx)
            price = price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            prices.append(str(price))
    else:
        if increment_value is None or increment_value <= 0:
            return None, "Enter a valid increment."
        current = min_value
        while current <= max_value:
            price = current.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            prices.append(str(price))
            current += increment_value

    return {
        "min_price": str(min_value),
        "max_price": str(max_value),
        "count": len(prices),
        "prices": prices,
        "steps": steps if steps and steps >= 2 else None,
        "increment": str(increment_value) if increment_value else None,
    }, None
