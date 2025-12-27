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


def calculate_break_even(
    fixed_costs: Any,
    price: Any,
    variable_cost: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    fixed_dec, error = _parse_decimal(fixed_costs)
    if error or fixed_dec is None:
        return None, error

    price_dec, error = _parse_decimal(price)
    if error or price_dec is None:
        return None, error

    variable_dec, error = _parse_decimal(variable_cost)
    if error or variable_dec is None:
        return None, error

    if fixed_dec < Decimal("0"):
        return None, "Fixed costs must be zero or higher."
    if price_dec <= Decimal("0"):
        return None, "Price must be greater than zero."
    if variable_dec < Decimal("0"):
        return None, "Variable cost must be zero or higher."
    if variable_dec >= price_dec:
        return None, "Variable cost must be lower than price."

    contribution = price_dec - variable_dec
    break_even_units = fixed_dec / contribution
    break_even_revenue = break_even_units * price_dec
    contribution_ratio = (contribution / price_dec) * Decimal("100")

    return {
        "fixed_costs": _quantize(fixed_dec, decimals),
        "price": _quantize(price_dec, decimals),
        "variable_cost": _quantize(variable_dec, decimals),
        "contribution": _quantize(contribution, decimals),
        "contribution_ratio": _quantize(contribution_ratio, decimals),
        "break_even_units": _quantize(break_even_units, decimals),
        "break_even_revenue": _quantize(break_even_revenue, decimals),
    }, None
