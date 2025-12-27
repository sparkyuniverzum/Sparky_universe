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


def _group_thousands(value: str, sep: str) -> str:
    if not sep:
        return value
    parts = []
    while value:
        parts.append(value[-3:])
        value = value[:-3]
    return sep.join(reversed(parts))


def format_money(
    value: Any,
    *,
    decimals: int = 2,
    thousand_sep: str = " ",
    decimal_sep: str = ",",
    currency: str = "",
    position: str = "suffix",
) -> Tuple[Dict[str, str] | None, str | None]:
    decimal, error = _parse_decimal(value)
    if error or decimal is None:
        return None, error

    decimals = max(0, min(int(decimals), 6))
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    rounded = decimal.quantize(quant, rounding=ROUND_HALF_UP)
    normalized = format(rounded, "f")

    if "." in normalized:
        integer_part, fraction = normalized.split(".", 1)
    else:
        integer_part, fraction = normalized, ""

    sign = ""
    if integer_part.startswith("-"):
        sign = "-"
        integer_part = integer_part[1:]

    grouped = _group_thousands(integer_part, thousand_sep)
    if decimals > 0:
        number = f"{sign}{grouped}{decimal_sep}{fraction}"
    else:
        number = f"{sign}{grouped}"

    currency = currency.strip()
    if currency:
        if position == "prefix":
            formatted = f"{currency} {number}"
        else:
            formatted = f"{number} {currency}"
    else:
        formatted = number

    return {"formatted": formatted, "normalized": normalized}, None
