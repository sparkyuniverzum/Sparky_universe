from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple


MAX_ITEMS = 5000


def _parse_decimal(value: Any, *, label: str) -> Tuple[Decimal | None, str | None]:
    if value is None:
        return None, f"{label} is required."
    raw = str(value).strip()
    if not raw:
        return None, f"{label} is required."

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


def _parse_int(value: Any, *, label: str) -> Tuple[int | None, str | None]:
    if value is None:
        return None, f"{label} is required."
    raw = str(value).strip()
    if not raw:
        return None, f"{label} is required."
    try:
        number = int(raw)
    except ValueError:
        return None, f"{label} must be a whole number."
    return number, None


def generate_range(
    start: Any,
    end: Any,
    step: Any,
    *,
    include_end: bool = True,
    decimals: int = 0,
) -> Tuple[Dict[str, Any] | None, str | None]:
    start_dec, error = _parse_decimal(start, label="Start")
    if error or start_dec is None:
        return None, error

    end_dec, error = _parse_decimal(end, label="End")
    if error or end_dec is None:
        return None, error

    step_dec, error = _parse_decimal(step, label="Step")
    if error or step_dec is None:
        return None, error

    if step_dec == Decimal("0"):
        return None, "Step must not be zero."

    decimals_int, error = _parse_int(decimals, label="Decimals")
    if error or decimals_int is None:
        return None, error
    if decimals_int < 0 or decimals_int > 6:
        return None, "Decimals must be between 0 and 6."

    direction = Decimal("1") if end_dec >= start_dec else Decimal("-1")
    if step_dec * direction <= 0:
        return None, "Step must move toward the end value."

    quant = Decimal("1") if decimals_int == 0 else Decimal("1." + "0" * decimals_int)

    items: List[str] = []
    current = start_dec
    count = 0

    def should_continue(value: Decimal) -> bool:
        if direction > 0:
            return value <= end_dec if include_end else value < end_dec
        return value >= end_dec if include_end else value > end_dec

    while should_continue(current):
        items.append(str(current.quantize(quant)))
        count += 1
        if count > MAX_ITEMS:
            return None, f"Too many items (limit {MAX_ITEMS})."
        current += step_dec

    return {
        "start": str(start_dec.quantize(quant)),
        "end": str(end_dec.quantize(quant)),
        "step": str(step_dec.quantize(quant)),
        "include_end": bool(include_end),
        "count": count,
        "values": items,
    }, None
