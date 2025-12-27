from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Tuple


def _parse_decimal(value: Any) -> Tuple[Decimal | None, str | None]:
    if value is None:
        return None, "Value is required."
    raw = str(value).strip()
    if not raw:
        return None, "Value is required."

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


def _quantize(value: Decimal, decimals: int = 2) -> str:
    decimals = max(0, min(int(decimals), 6))
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def convert_currency(
    amount: Any,
    rate: Any,
    *,
    direction: str = "multiply",
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    amount_dec, error = _parse_decimal(amount)
    if error or amount_dec is None:
        return None, error

    rate_dec, error = _parse_decimal(rate)
    if error or rate_dec is None:
        return None, error

    if rate_dec <= Decimal("0"):
        return None, "Rate must be greater than zero."

    if direction == "divide":
        result = amount_dec / rate_dec
        formula = "amount / rate"
    else:
        result = amount_dec * rate_dec
        formula = "amount * rate"

    return {
        "amount": _quantize(amount_dec, decimals),
        "rate": _quantize(rate_dec, decimals),
        "result": _quantize(result, decimals),
        "direction": direction,
        "formula": formula,
    }, None
