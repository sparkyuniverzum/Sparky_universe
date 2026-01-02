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


def _quantize(value: Decimal, decimals: int = 4) -> str:
    decimals = max(0, min(int(decimals), 10))
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def calc_roi(
    cost: Any,
    return_value: Any,
) -> Tuple[Dict[str, str] | None, str | None]:
    cost_dec, error = _parse_decimal(cost)
    if error or cost_dec is None:
        return None, error
    return_dec, error = _parse_decimal(return_value)
    if error or return_dec is None:
        return None, error
    if cost_dec <= 0:
        return None, "Cost must be greater than zero."

    net = return_dec - cost_dec
    roi = (net / cost_dec) * Decimal("100")

    return {
        "cost": _quantize(cost_dec, 2),
        "return": _quantize(return_dec, 2),
        "net_profit": _quantize(net, 2),
        "roi_percent": _quantize(roi, 2),
    }, None

