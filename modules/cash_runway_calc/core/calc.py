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


def calc_runway(
    cash: Any,
    monthly_burn: Any,
) -> Tuple[Dict[str, str] | None, str | None]:
    cash_dec, error = _parse_decimal(cash)
    if error or cash_dec is None:
        return None, error
    burn_dec, error = _parse_decimal(monthly_burn)
    if error or burn_dec is None:
        return None, error
    if cash_dec < 0:
        return None, "Cash must be zero or higher."
    if burn_dec <= 0:
        return None, "Monthly burn must be greater than zero."

    runway = cash_dec / burn_dec
    buffer = burn_dec * Decimal("3")

    return {
        "cash": _quantize(cash_dec, 2),
        "monthly_burn": _quantize(burn_dec, 2),
        "runway_months": _quantize(runway, 2),
        "recommended_buffer": _quantize(buffer, 2),
    }, None

