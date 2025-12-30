from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, List, Tuple


MAX_ITEMS = 50


def _parse_decimal(value: object, *, label: str) -> Tuple[Decimal | None, str | None]:
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
        return None, f"{label} must be a number."


def _parse_int(value: object, *, label: str, default: int) -> Tuple[int, str | None]:
    if value is None:
        return default, None
    raw = str(value).strip()
    if not raw:
        return default, None
    try:
        return int(raw), None
    except ValueError:
        return default, f"{label} must be a whole number."


def _quantize(value: Decimal, decimals: int) -> str:
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def _to_minor_units(value: Decimal, decimals: int) -> int:
    scale = Decimal(10) ** decimals
    return int((value * scale).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _from_minor_units(value: int, decimals: int) -> str:
    scale = Decimal(10) ** decimals
    return _quantize(Decimal(value) / scale, decimals)


def _parse_weights(raw: object) -> Tuple[List[Decimal] | None, str | None]:
    if raw is None:
        return None, "Weights are required."
    text = str(raw).strip()
    if not text:
        return None, "Weights are required."

    tokens = [token for token in re.split(r"[,\s]+", text) if token]
    if not tokens:
        return None, "Weights are required."
    if len(tokens) > MAX_ITEMS:
        return None, f"Too many weights (limit {MAX_ITEMS})."

    weights: List[Decimal] = []
    for token in tokens:
        value, error = _parse_decimal(token, label="Weight")
        if error or value is None:
            return None, error
        if value < 0:
            return None, "Weights must be non-negative."
        weights.append(value)

    if all(weight == 0 for weight in weights):
        return None, "At least one weight must be positive."
    return weights, None


def split_weighted(
    amount: object,
    weights: object,
    *,
    mode: object = "weights",
    decimals: object = 2,
) -> Tuple[Dict[str, object] | None, str | None]:
    amount_dec, error = _parse_decimal(amount, label="Amount")
    if error or amount_dec is None:
        return None, error

    if amount_dec < Decimal("0"):
        return None, "Amount must be non-negative."

    decimals_int, error = _parse_int(decimals, label="Decimals", default=2)
    if error:
        return None, error
    if decimals_int < 0 or decimals_int > 4:
        return None, "Decimals must be between 0 and 4."

    weights_list, error = _parse_weights(weights)
    if error or weights_list is None:
        return None, error

    mode_key = str(mode or "weights").strip().lower()
    if mode_key not in {"weights", "percent"}:
        return None, "Mode must be weights or percent."

    total_weight = sum(weights_list, Decimal(0))
    if total_weight <= 0:
        return None, "Weights must add up to a positive value."

    if mode_key == "percent":
        if abs(total_weight - Decimal("100")) > Decimal("0.01"):
            return None, "Percent weights must sum to 100."

    total_units = _to_minor_units(amount_dec, decimals_int)

    raw_units: List[Tuple[int, Decimal]] = []
    allocated_units = 0
    for weight in weights_list:
        share = (Decimal(total_units) * weight) / total_weight
        floor_units = int(share)
        allocated_units += floor_units
        raw_units.append((floor_units, share - Decimal(floor_units)))

    remainder = total_units - allocated_units
    if remainder != 0:
        order = sorted(
            range(len(raw_units)),
            key=lambda i: raw_units[i][1],
            reverse=remainder > 0,
        )
        step = 1 if remainder > 0 else -1
        for idx in order[: abs(remainder)]:
            base_units, frac = raw_units[idx]
            raw_units[idx] = (base_units + step, frac)

    parts: List[Dict[str, object]] = []
    for idx, (units, _) in enumerate(raw_units, start=1):
        parts.append(
            {
                "index": idx,
                "weight": str(weights_list[idx - 1]),
                "amount": _from_minor_units(units, decimals_int),
            }
        )

    return {
        "total": _quantize(amount_dec, decimals_int),
        "weights_sum": str(total_weight),
        "decimals": decimals_int,
        "parts": parts,
    }, None
