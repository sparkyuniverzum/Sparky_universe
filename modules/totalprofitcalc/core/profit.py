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


def calculate_total_profit(
    price: Any,
    cost: Any,
    quantity: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    price_dec, error = _parse_decimal(price)
    if error or price_dec is None:
        return None, error

    cost_dec, error = _parse_decimal(cost)
    if error or cost_dec is None:
        return None, error

    quantity_dec, error = _parse_decimal(quantity)
    if error or quantity_dec is None:
        return None, error

    if price_dec < Decimal("0"):
        return None, "Price must be zero or higher."
    if cost_dec < Decimal("0"):
        return None, "Cost must be zero or higher."
    if quantity_dec < Decimal("0"):
        return None, "Quantity must be zero or higher."

    revenue = price_dec * quantity_dec
    total_cost = cost_dec * quantity_dec
    profit = revenue - total_cost

    if revenue == Decimal("0"):
        margin_percent = Decimal("0")
    else:
        margin_percent = (profit / revenue) * Decimal("100")

    if total_cost == Decimal("0"):
        markup_percent = Decimal("0")
    else:
        markup_percent = (profit / total_cost) * Decimal("100")

    return {
        "price": _quantize(price_dec, decimals),
        "cost": _quantize(cost_dec, decimals),
        "quantity": _quantize(quantity_dec, decimals),
        "revenue": _quantize(revenue, decimals),
        "total_cost": _quantize(total_cost, decimals),
        "profit": _quantize(profit, decimals),
        "margin_percent": _quantize(margin_percent, decimals),
        "markup_percent": _quantize(markup_percent, decimals),
    }, None
