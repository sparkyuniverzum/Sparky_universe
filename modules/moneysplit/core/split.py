from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple


def _parse_decimal(value: Any) -> Tuple[Decimal | None, str | None]:
    if value is None:
        return None, "Amount is required."
    raw = str(value).strip()
    if not raw:
        return None, "Amount is required."

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


def _parse_parts(value: Any) -> Tuple[int | None, str | None]:
    if value is None:
        return None, "Parts is required."
    raw = str(value).strip()
    if not raw:
        return None, "Parts is required."
    try:
        parts = int(raw)
    except ValueError:
        return None, "Parts must be a whole number."
    if parts <= 0:
        return None, "Parts must be greater than zero."
    return parts, None


def _quantize(value: Decimal, decimals: int = 2) -> str:
    decimals = max(0, min(int(decimals), 6))
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def _to_minor_units(value: Decimal, decimals: int) -> int:
    scale = Decimal(10) ** decimals
    return int((value * scale).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _from_minor_units(value: int, decimals: int) -> str:
    scale = Decimal(10) ** decimals
    return _quantize(Decimal(value) / scale, decimals)


def calculate_split(
    amount: Any,
    parts: Any,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, Any] | None, str | None]:
    amount_dec, error = _parse_decimal(amount)
    if error or amount_dec is None:
        return None, error

    parts_int, error = _parse_parts(parts)
    if error or parts_int is None:
        return None, error

    if amount_dec < Decimal("0"):
        return None, "Amount must be zero or higher."

    decimals = max(0, min(int(decimals), 6))
    total_units = _to_minor_units(amount_dec, decimals)

    base_units = total_units // parts_int
    remainder_units = total_units % parts_int

    parts_list: List[str] = []
    for index in range(parts_int):
        unit_value = base_units + (1 if index < remainder_units else 0)
        parts_list.append(_from_minor_units(unit_value, decimals))

    return {
        "total": _quantize(amount_dec, decimals),
        "parts_count": parts_int,
        "base_part": _from_minor_units(base_units, decimals),
        "remainder_parts": int(remainder_units),
        "remainder_total": _from_minor_units(remainder_units, decimals),
        "parts": parts_list,
    }, None
