from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Tuple


def _parse_decimal(value: Any, *, label: str) -> Tuple[Decimal | None, str | None]:
    if value is None:
        return None, f"{label} is required."
    raw = str(value).strip()
    if not raw:
        return None, f"{label} is required."

    compact = raw.replace(" ", "")
    if "," in compact and "." in compact:
        last_comma = compact.rfind(",")
        last_dot = compact.rfind(".")
        if last_comma > last_dot:
            compact = compact.replace(".", "")
            compact = compact.replace(",", ".")
        else:
            compact = compact.replace(",", "")
    elif "," in compact:
        compact = compact.replace(",", ".")

    try:
        return Decimal(compact), None
    except (InvalidOperation, ValueError):
        return None, "Invalid number format."


def _parse_int(value: Any, *, label: str) -> Tuple[int | None, str | None]:
    if value is None:
        return None, f"{label} is required."
    raw = str(value).strip()
    if not raw:
        return None, f"{label} is required."
    try:
        number = int(raw)
    except ValueError:
        return None, f"{label} must be a whole number."
    if number <= 0:
        return None, f"{label} must be greater than zero."
    return number, None


def _quantize(value: Decimal, decimals: int = 2) -> str:
    decimals = max(0, min(int(decimals), 6))
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def calculate_tip_split(
    amount: Any,
    tip_percent: Any,
    people: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    amount_dec, error = _parse_decimal(amount, label="Amount")
    if error or amount_dec is None:
        return None, error

    tip_dec, error = _parse_decimal(tip_percent, label="Tip percent")
    if error or tip_dec is None:
        return None, error

    people_int, error = _parse_int(people, label="People")
    if error or people_int is None:
        return None, error

    if amount_dec < Decimal("0"):
        return None, "Amount must be zero or higher."
    if tip_dec < Decimal("0"):
        return None, "Tip percent must be zero or higher."

    tip_amount = amount_dec * (tip_dec / Decimal("100"))
    total = amount_dec + tip_amount
    per_person = total / Decimal(people_int)

    return {
        "amount": _quantize(amount_dec, decimals),
        "tip_percent": _quantize(tip_dec, decimals),
        "tip_amount": _quantize(tip_amount, decimals),
        "total": _quantize(total, decimals),
        "people": str(people_int),
        "per_person": _quantize(per_person, decimals),
    }, None
