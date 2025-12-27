from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Tuple

Q4 = Decimal("0.0001")
Q3 = Decimal("0.001")
Q2 = Decimal("0.01")


def _sanitize(value: str) -> str:
    return value.strip().replace(" ", "").replace(",", ".")


def _parse_decimal(value: Any) -> Tuple[Decimal | None, str | None]:
    if value is None:
        return None, "Value is required."
    raw = str(value)
    if not raw.strip():
        return None, "Value is required."

    normalized = _sanitize(raw)
    try:
        return Decimal(normalized), None
    except (InvalidOperation, ValueError):
        return None, "Invalid number format."


def format_number(value: Any) -> Tuple[Dict[str, str] | None, str | None]:
    decimal, error = _parse_decimal(value)
    if error or decimal is None:
        return None, error

    result = {
        "normalized": _sanitize(str(value)),
        "money_out": format(decimal, "f"),
        "q2": str(decimal.quantize(Q2, rounding=ROUND_HALF_UP)),
        "q3": str(decimal.quantize(Q3, rounding=ROUND_HALF_UP)),
        "q4": str(decimal.quantize(Q4, rounding=ROUND_HALF_UP)),
    }
    return result, None
