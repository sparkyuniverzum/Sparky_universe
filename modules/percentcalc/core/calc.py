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


def calculate_percent(
    base: Any,
    value: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    base_dec, error = _parse_decimal(base)
    if error or base_dec is None:
        return None, error

    value_dec, error = _parse_decimal(value)
    if error or value_dec is None:
        return None, error

    if base_dec == Decimal("0"):
        return None, "Base value must not be zero."

    ratio = (value_dec / base_dec) * Decimal("100")
    change = value_dec - base_dec
    change_pct = (change / base_dec) * Decimal("100")

    return {
        "ratio_percent": _quantize(ratio, decimals),
        "change": _quantize(change, decimals),
        "change_percent": _quantize(change_pct, decimals),
        "base": _quantize(base_dec, decimals),
        "value": _quantize(value_dec, decimals),
    }, None


def calculate_percent_of(
    base: Any,
    percent: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    base_dec, error = _parse_decimal(base)
    if error or base_dec is None:
        return None, error

    percent_dec, error = _parse_decimal(percent)
    if error or percent_dec is None:
        return None, "Invalid percent value."

    result = base_dec * (percent_dec / Decimal("100"))
    return {
        "result": _quantize(result, decimals),
        "percent": _quantize(percent_dec, decimals),
        "base": _quantize(base_dec, decimals),
    }, None
