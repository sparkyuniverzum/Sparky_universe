from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple


@dataclass
class ResultBlock:
    label: str
    value: float | int | str
    unit: str | None = None


def _parse_decimal(
    value: str | None, name: str, minimum: Decimal | None
) -> Tuple[Decimal | None, str | None]:
    if value is None or str(value).strip() == "":
        return None, f"{name} is required."
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None, f"{name} must be a number."
    if minimum is not None and parsed < minimum:
        return None, f"{name} must be at least {minimum}."
    return parsed, None


def _parse_int(value: str | None, name: str, minimum: int) -> Tuple[int | None, str | None]:
    if value is None or str(value).strip() == "":
        return None, f"{name} is required."
    try:
        parsed = int(str(value))
    except ValueError:
        return None, f"{name} must be a whole number."
    if parsed < minimum:
        return None, f"{name} must be at least {minimum}."
    return parsed, None


def _quantize(value: Decimal, places: int) -> Decimal:
    scale = Decimal("1").scaleb(-places)
    return value.quantize(scale, rounding=ROUND_HALF_UP)


def _as_float(value: Decimal, places: int = 2) -> float:
    return float(_quantize(value, places))


def _as_text(value: Decimal, places: int = 2) -> str:
    return f"{_quantize(value, places):.{places}f}"


def _make_payload(
    *,
    intent: str,
    primary: ResultBlock,
    secondary: List[ResultBlock],
    sparky_line: str,
) -> Dict[str, Any]:
    return {
        "intent": intent,
        "primary": {
            "label": primary.label,
            "value": primary.value,
            "unit": primary.unit,
        },
        "secondary": [
            {"label": item.label, "value": item.value, "unit": item.unit}
            for item in secondary
        ],
        "sparky": sparky_line,
    }


def calculate_packer_need(
    orders_raw: str | None,
    minutes_per_order_raw: str | None,
    hours_available_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    orders, error = _parse_int(orders_raw, "Orders", 1)
    if error:
        return None, error
    minutes, error = _parse_decimal(minutes_per_order_raw, "Minutes per order", Decimal("0.1"))
    if error:
        return None, error
    hours, error = _parse_decimal(hours_available_raw, "Hours available", Decimal("0.1"))
    if error:
        return None, error

    total_minutes = Decimal(orders) * minutes
    capacity_minutes = hours * Decimal("60")
    packers_needed = math.ceil(float(total_minutes / capacity_minutes))
    orders_per_packer = Decimal(orders) / Decimal(packers_needed)

    primary = ResultBlock("Packers needed", packers_needed)
    secondary = [ResultBlock("Orders per packer", _as_float(orders_per_packer, 1))]
    sparky_line = f"Packers needed: {packers_needed}."
    return _make_payload(
        intent="packer_need",
        primary=primary,
        secondary=secondary,
        sparky_line=sparky_line,
    ), None


def calculate_cutoff(
    orders_left_raw: str | None,
    minutes_per_order_raw: str | None,
    packers_available_raw: str | None,
    hours_left_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    orders_left, error = _parse_int(orders_left_raw, "Orders left", 1)
    if error:
        return None, error
    minutes, error = _parse_decimal(minutes_per_order_raw, "Minutes per order", Decimal("0.1"))
    if error:
        return None, error
    packers, error = _parse_int(packers_available_raw, "Packers available", 1)
    if error:
        return None, error
    hours_left, error = _parse_decimal(hours_left_raw, "Hours left", Decimal("0.1"))
    if error:
        return None, error

    total_minutes = Decimal(orders_left) * minutes
    capacity_minutes = Decimal(packers) * Decimal("60")
    hours_needed = total_minutes / capacity_minutes
    slack = hours_left - hours_needed

    primary = ResultBlock("Hours needed", _as_float(hours_needed, 2), "h")
    secondary = [ResultBlock("Slack hours", _as_float(slack, 2), "h")]
    sparky_line = f"Hours needed: {_as_text(hours_needed, 2)}."
    return _make_payload(
        intent="cutoff_check",
        primary=primary,
        secondary=secondary,
        sparky_line=sparky_line,
    ), None


def calculate_pick_list(
    orders_raw: str | None,
    items_per_order_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    orders, error = _parse_int(orders_raw, "Orders", 1)
    if error:
        return None, error
    items_per_order, error = _parse_decimal(
        items_per_order_raw, "Items per order", Decimal("0.1")
    )
    if error:
        return None, error

    total_items = Decimal(orders) * items_per_order

    primary = ResultBlock("Items to pick", _as_float(total_items, 1))
    secondary = [ResultBlock("Items per order", _as_float(items_per_order, 1))]
    sparky_line = f"Items to pick: {_as_text(total_items, 1)}."
    return _make_payload(
        intent="pick_list",
        primary=primary,
        secondary=secondary,
        sparky_line=sparky_line,
    ), None


def calculate_packaging_buffer(
    orders_raw: str | None,
    buffer_percent_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    orders, error = _parse_int(orders_raw, "Orders", 1)
    if error:
        return None, error
    buffer_percent, error = _parse_decimal(
        buffer_percent_raw, "Buffer percent", Decimal("0")
    )
    if error:
        return None, error

    buffer = (Decimal(orders) * buffer_percent) / Decimal("100")
    buffer_count = int(math.ceil(float(buffer)))
    total = orders + buffer_count

    primary = ResultBlock("Packages to prep", total)
    secondary = [ResultBlock("Buffer count", buffer_count)]
    sparky_line = f"Packages to prep: {total}."
    return _make_payload(
        intent="packaging",
        primary=primary,
        secondary=secondary,
        sparky_line=sparky_line,
    ), None
