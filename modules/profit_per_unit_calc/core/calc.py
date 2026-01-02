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


def calc_unit_profit(
    price: Any,
    cost: Any,
    fees: Any,
) -> Tuple[Dict[str, str] | None, str | None]:
    price_dec, error = _parse_decimal(price)
    if error or price_dec is None:
        return None, error
    cost_dec, error = _parse_decimal(cost)
    if error or cost_dec is None:
        return None, error
    fees_dec, error = _parse_decimal(fees)
    if error or fees_dec is None:
        return None, error

    if price_dec <= 0:
        return None, "Price must be greater than zero."
    if cost_dec < 0 or fees_dec < 0:
        return None, "Costs and fees must be zero or higher."

    profit = price_dec - cost_dec - fees_dec
    margin = (profit / price_dec) * Decimal("100")

    return {
        "price": _quantize(price_dec, 2),
        "cost": _quantize(cost_dec, 2),
        "fees": _quantize(fees_dec, 2),
        "profit_per_unit": _quantize(profit, 2),
        "margin_percent": _quantize(margin, 2),
    }, None

