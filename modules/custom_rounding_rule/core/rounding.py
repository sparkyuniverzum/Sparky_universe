from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
from typing import Any, Dict, Tuple


def _parse_decimal(value: str | None) -> Tuple[Decimal | None, str | None]:
    if not value or not value.strip():
        return None, "Enter a value."
    cleaned = value.strip().replace(" ", "")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned), None
    except (InvalidOperation, ValueError):
        return None, "Value must be a number."


def apply_rounding(
    amount_raw: str | None,
    step_raw: str | None,
    *,
    mode: str = "nearest",
) -> Tuple[Dict[str, Any] | None, str | None]:
    amount, error = _parse_decimal(amount_raw)
    if error:
        return None, error
    step, error = _parse_decimal(step_raw)
    if error:
        return None, error
    assert amount is not None and step is not None

    if step <= 0:
        return None, "Step must be greater than zero."

    mode = (mode or "nearest").lower().strip()
    if mode not in {"nearest", "up", "down"}:
        return None, "Mode must be nearest, up, or down."

    rounding_mode = ROUND_HALF_UP
    if mode == "up":
        rounding_mode = ROUND_CEILING
    elif mode == "down":
        rounding_mode = ROUND_FLOOR

    quotient = (amount / step).quantize(Decimal("1"), rounding=rounding_mode)
    rounded = (quotient * step).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    difference = (rounded - amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "amount": str(amount),
        "step": str(step),
        "mode": mode,
        "rounded": str(rounded),
        "difference": str(difference),
    }, None
