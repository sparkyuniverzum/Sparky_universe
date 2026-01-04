from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Tuple


def _parse_decimal(value: Any, *, required: bool = True) -> Tuple[Decimal | None, str | None]:
    if value is None:
        return (None, "Value is required.") if required else (None, None)
    raw = str(value).strip()
    if not raw:
        return (None, "Value is required.") if required else (None, None)

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


def _comparison_payload(
    reference: Decimal,
    target: Decimal,
    *,
    label: str,
    decimals: int,
) -> Dict[str, str | None]:
    delta = target - reference
    delta_pct = None
    if reference != Decimal("0"):
        delta_pct = _quantize((delta / reference) * Decimal("100"), 2)
    return {
        "label": label,
        "reference": _quantize(reference, decimals),
        "delta": _quantize(delta, decimals),
        "delta_percent": delta_pct,
    }


def annual_breakdown(
    annual_income: Any,
    current_monthly: Any = None,
    average_monthly: Any = None,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str | Dict[str, str | None] | None] | None, str | None]:
    annual_dec, error = _parse_decimal(annual_income)
    if error or annual_dec is None:
        return None, error
    if annual_dec <= Decimal("0"):
        return None, "Annual income must be greater than zero."

    monthly_target = annual_dec / Decimal("12")
    daily_target = annual_dec / Decimal("365")

    comparison = None
    current_dec, error = _parse_decimal(current_monthly, required=False)
    if error:
        return None, error
    if current_dec is not None:
        comparison = _comparison_payload(
            current_dec,
            monthly_target,
            label="Current monthly pace",
            decimals=decimals,
        )
    else:
        average_dec, error = _parse_decimal(average_monthly, required=False)
        if error:
            return None, error
        if average_dec is not None:
            comparison = _comparison_payload(
                average_dec,
                monthly_target,
                label="Average monthly benchmark",
                decimals=decimals,
            )

    return {
        "annual_target": _quantize(annual_dec, decimals),
        "monthly_target": _quantize(monthly_target, decimals),
        "daily_target": _quantize(daily_target, decimals),
        "comparison": comparison,
    }, None
