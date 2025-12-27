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


def calculate_discount(
    original: Any,
    percent: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    original_dec, error = _parse_decimal(original)
    if error or original_dec is None:
        return None, error

    percent_dec, error = _parse_decimal(percent)
    if error or percent_dec is None:
        return None, error

    if original_dec <= Decimal("0"):
        return None, "Original price must be greater than zero."

    if percent_dec < Decimal("0") or percent_dec > Decimal("100"):
        return None, "Discount percent must be between 0 and 100."

    discount_amount = original_dec * (percent_dec / Decimal("100"))
    final_price = original_dec - discount_amount

    return {
        "original": _quantize(original_dec, decimals),
        "percent": _quantize(percent_dec, decimals),
        "discount": _quantize(discount_amount, decimals),
        "final": _quantize(final_price, decimals),
    }, None


def calculate_discount_from_final(
    original: Any,
    final: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    original_dec, error = _parse_decimal(original)
    if error or original_dec is None:
        return None, error

    final_dec, error = _parse_decimal(final)
    if error or final_dec is None:
        return None, error

    if original_dec <= Decimal("0"):
        return None, "Original price must be greater than zero."

    if final_dec < Decimal("0"):
        return None, "Final price must be zero or higher."

    if final_dec > original_dec:
        return None, "Final price must be less than or equal to original."

    discount_amount = original_dec - final_dec
    percent = (discount_amount / original_dec) * Decimal("100")

    return {
        "original": _quantize(original_dec, decimals),
        "final": _quantize(final_dec, decimals),
        "discount": _quantize(discount_amount, decimals),
        "percent": _quantize(percent, decimals),
    }, None
