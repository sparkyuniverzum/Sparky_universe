from __future__ import annotations

from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_CEILING,
    ROUND_FLOOR,
    ROUND_HALF_UP,
)
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


def _round_value(value: Decimal, decimals: int, mode: str) -> Decimal:
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    if mode == "ceil":
        return value.quantize(quant, rounding=ROUND_CEILING)
    if mode == "floor":
        return value.quantize(quant, rounding=ROUND_FLOOR)
    return value.quantize(quant, rounding=ROUND_HALF_UP)


def round_number(
    value: Any,
    *,
    decimals: int = 2,
    mode: str = "round",
) -> Tuple[Dict[str, str] | None, str | None]:
    value_dec, error = _parse_decimal(value)
    if error or value_dec is None:
        return None, error

    decimals = max(0, min(int(decimals), 8))
    mode_key = mode.lower().strip()
    if mode_key not in {"round", "ceil", "floor"}:
        return None, "Unknown rounding mode."

    rounded = _round_value(value_dec, decimals, mode_key)
    delta = rounded - value_dec

    return {
        "value": str(value_dec),
        "rounded": str(rounded),
        "decimals": str(decimals),
        "mode": mode_key,
        "delta": str(delta),
    }, None
