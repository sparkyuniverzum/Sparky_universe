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


def calc_small_change_impact(
    income: Any,
    costs: Any,
    change_percent: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    income_dec, error = _parse_decimal(income)
    if error or income_dec is None:
        return None, error

    costs_dec, error = _parse_decimal(costs)
    if error or costs_dec is None:
        return None, error

    change_dec, error = _parse_decimal(change_percent)
    if error or change_dec is None:
        return None, "Invalid change percent."

    baseline_profit = income_dec - costs_dec
    multiplier = Decimal("1") + (change_dec / Decimal("100"))
    new_costs = costs_dec * multiplier
    new_profit = income_dec - new_costs
    monthly_impact = new_profit - baseline_profit

    return {
        "baseline_profit": _quantize(baseline_profit, decimals),
        "new_profit": _quantize(new_profit, decimals),
        "monthly_impact": _quantize(monthly_impact, decimals),
        "yearly_impact": _quantize(monthly_impact * Decimal("12"), decimals),
        "three_year_impact": _quantize(monthly_impact * Decimal("36"), decimals),
        "income": _quantize(income_dec, decimals),
        "costs": _quantize(costs_dec, decimals),
        "change_percent": _quantize(change_dec, 2),
    }, None
