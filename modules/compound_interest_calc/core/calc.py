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


def calc_compound(
    principal: Any,
    annual_rate: Any,
    years: Any,
    compounds_per_year: Any,
) -> Tuple[Dict[str, str] | None, str | None]:
    principal_dec, error = _parse_decimal(principal)
    if error or principal_dec is None:
        return None, error
    rate_dec, error = _parse_decimal(annual_rate)
    if error or rate_dec is None:
        return None, error
    years_dec, error = _parse_decimal(years)
    if error or years_dec is None:
        return None, error
    comp_dec, error = _parse_decimal(compounds_per_year)
    if error or comp_dec is None:
        return None, error

    if principal_dec < 0:
        return None, "Principal must be zero or higher."
    if years_dec <= 0:
        return None, "Years must be greater than zero."
    if comp_dec <= 0:
        return None, "Compounds per year must be greater than zero."
    if rate_dec < 0:
        return None, "Rate must be zero or higher."

    rate = rate_dec / Decimal("100")
    comp_per_year = comp_dec
    exponent = comp_per_year * years_dec
    factor = (Decimal("1") + rate / comp_per_year) ** exponent
    future_value = principal_dec * factor
    interest = future_value - principal_dec

    return {
        "principal": _quantize(principal_dec, 2),
        "future_value": _quantize(future_value, 2),
        "interest_earned": _quantize(interest, 2),
        "years": _quantize(years_dec, 2),
        "compounds_per_year": _quantize(comp_per_year, 0),
    }, None

