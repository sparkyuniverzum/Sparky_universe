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


def calculate_markup(
    cost: Any,
    price: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    cost_dec, error = _parse_decimal(cost)
    if error or cost_dec is None:
        return None, error

    price_dec, error = _parse_decimal(price)
    if error or price_dec is None:
        return None, error

    if cost_dec <= Decimal("0"):
        return None, "Cost must be greater than zero."
    if price_dec <= Decimal("0"):
        return None, "Price must be greater than zero."

    profit = price_dec - cost_dec
    markup = (profit / cost_dec) * Decimal("100")

    return {
        "cost": _quantize(cost_dec, decimals),
        "price": _quantize(price_dec, decimals),
        "profit": _quantize(profit, decimals),
        "markup_percent": _quantize(markup, decimals),
    }, None


def calculate_price_from_markup(
    cost: Any,
    markup_percent: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    cost_dec, error = _parse_decimal(cost)
    if error or cost_dec is None:
        return None, error

    markup_dec, error = _parse_decimal(markup_percent)
    if error or markup_dec is None:
        return None, error

    if cost_dec <= Decimal("0"):
        return None, "Cost must be greater than zero."
    if markup_dec < Decimal("0"):
        return None, "Markup percent must be zero or higher."

    multiplier = Decimal("1") + (markup_dec / Decimal("100"))
    price_dec = cost_dec * multiplier
    profit = price_dec - cost_dec

    return {
        "cost": _quantize(cost_dec, decimals),
        "price": _quantize(price_dec, decimals),
        "profit": _quantize(profit, decimals),
        "markup_percent": _quantize(markup_dec, decimals),
    }, None
