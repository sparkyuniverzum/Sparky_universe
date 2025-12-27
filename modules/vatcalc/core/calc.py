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


def calculate_vat(
    amount: Any,
    rate: Any,
    *,
    mode: str = "net",
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    amount_dec, error = _parse_decimal(amount)
    if error or amount_dec is None:
        return None, error

    rate_dec, error = _parse_decimal(rate)
    if error or rate_dec is None:
        return None, "Invalid VAT rate."

    if rate_dec < 0:
        return None, "VAT rate must be positive."

    multiplier = rate_dec / Decimal("100")

    if mode == "gross":
        net = amount_dec / (Decimal("1") + multiplier)
        vat = amount_dec - net
        gross = amount_dec
    else:
        net = amount_dec
        vat = amount_dec * multiplier
        gross = amount_dec + vat

    return {
        "net": _quantize(net, decimals),
        "vat": _quantize(vat, decimals),
        "gross": _quantize(gross, decimals),
        "rate": _quantize(rate_dec, 2),
    }, None
