from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple


@dataclass
class ResultBlock:
    label: str
    value: float | str
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


def calculate_labels(
    orders_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    orders, error = _parse_int(orders_raw, "Orders", 1)
    if error:
        return None, error

    primary = ResultBlock("Labels to print", float(orders))
    sparky_line = f"Labels needed: {orders}."
    return _make_payload(
        intent="labels",
        primary=primary,
        secondary=[],
        sparky_line=sparky_line,
    ), None


def calculate_slots(
    orders_raw: str | None,
    slots_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    orders, error = _parse_int(orders_raw, "Orders", 1)
    if error:
        return None, error
    slots, error = _parse_int(slots_raw, "Slots", 1)
    if error:
        return None, error

    per_slot = orders // slots
    remainder = orders % slots

    primary = ResultBlock("Orders per slot", float(per_slot))
    secondary = [ResultBlock("Remainder", float(remainder))]
    sparky_line = f"Plan for {per_slot} orders per slot."
    return _make_payload(
        intent="slot_split",
        primary=primary,
        secondary=secondary,
        sparky_line=sparky_line,
    ), None


def _clean_token(value: str) -> str:
    cleaned = "".join(ch for ch in value.strip() if ch.isalnum() or ch in {"-", "_"})
    cleaned = cleaned.replace(" ", "-").replace("--", "-")
    return cleaned.strip("-_")


def _default_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def calculate_batch_id(
    name_raw: str | None,
    date_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    name = (name_raw or "").strip()
    if not name:
        return None, "Batch name is required."

    name_token = _clean_token(name).upper() or "BATCH"
    date_token = _clean_token(date_raw or "")
    if date_raw and not date_token:
        return None, "Date must include letters or digits, or leave it blank."

    date_value = date_token.upper() if date_token else _default_date()
    batch_id = f"{name_token}-{date_value}"

    primary = ResultBlock("Batch ID", batch_id)
    sparky_line = f"Batch ID ready: {batch_id}."
    return _make_payload(
        intent="batch_id",
        primary=primary,
        secondary=[],
        sparky_line=sparky_line,
    ), None


def calculate_missing(
    planned_raw: str | None,
    current_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    planned, error = _parse_decimal(planned_raw, "Planned items", Decimal("1"))
    if error:
        return None, error
    current, error = _parse_decimal(current_raw, "Current items", Decimal("0"))
    if error:
        return None, error

    missing = planned - current
    if missing < 0:
        missing = Decimal("0")

    completion = (current / planned) * Decimal("100")

    primary = ResultBlock("Missing items", _as_float(missing))
    secondary = [ResultBlock("Completion", _as_float(completion, 1), "%")]
    sparky_line = f"Missing items: {_as_text(missing)}."
    return _make_payload(
        intent="missing_check",
        primary=primary,
        secondary=secondary,
        sparky_line=sparky_line,
    ), None
