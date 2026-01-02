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


def calc_payment(
    principal: Any,
    annual_rate: Any,
    years: Any,
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
    if principal_dec <= 0:
        return None, "Principal must be greater than zero."
    if years_dec <= 0:
        return None, "Years must be greater than zero."
    if rate_dec < 0:
        return None, "Rate must be zero or higher."

    months = int((years_dec * Decimal("12")).to_integral_value(rounding=ROUND_HALF_UP))
    if months <= 0:
        return None, "Loan term is too short."

    monthly_rate = rate_dec / Decimal("100") / Decimal("12")
    if monthly_rate == 0:
        payment = principal_dec / Decimal(months)
    else:
        factor = (Decimal("1") + monthly_rate) ** months
        payment = principal_dec * monthly_rate * factor / (factor - Decimal("1"))

    total_paid = payment * Decimal(months)
    total_interest = total_paid - principal_dec

    return {
        "principal": _quantize(principal_dec, 2),
        "months": str(months),
        "monthly_payment": _quantize(payment, 2),
        "total_paid": _quantize(total_paid, 2),
        "total_interest": _quantize(total_interest, 2),
    }, None

