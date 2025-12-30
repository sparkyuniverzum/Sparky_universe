from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_FLOOR, ROUND_HALF_UP
from typing import Dict, Tuple


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


def _parse_ending(raw: object, decimals: int) -> Tuple[Decimal | None, str | None]:
    if raw is None:
        return None, "Ending is required."
    text = str(raw).strip()
    if not text:
        return None, "Ending is required."

    normalized = text.replace(" ", "").replace(",", ".")
    if "." not in normalized and normalized.isdigit():
        value = Decimal(normalized)
        if value >= 1 and value < 100 and decimals >= 2:
            normalized = str(value / Decimal("100"))

    try:
        ending = Decimal(normalized)
    except (InvalidOperation, ValueError):
        return None, "Ending must be a number."

    if ending < 0 or ending >= 1:
        return None, "Ending must be between 0 and 1."
    return ending, None


def apply_ending(
    price: object,
    ending: object,
    *,
    mode: object = "round",
    decimals: object = 2,
) -> Tuple[Dict[str, object] | None, str | None]:
    price_dec, error = _parse_decimal(price, label="Price")
    if error or price_dec is None:
        return None, error
    if price_dec < Decimal("0"):
        return None, "Price must be non-negative."

    decimals_int, error = _parse_int(decimals, label="Decimals", default=2)
    if error:
        return None, error
    if decimals_int < 0 or decimals_int > 4:
        return None, "Decimals must be between 0 and 4."

    ending_dec, error = _parse_ending(ending, decimals_int)
    if error or ending_dec is None:
        return None, error

    mode_key = str(mode or "round").strip().lower()
    if mode_key not in {"round", "floor", "ceil"}:
        return None, "Mode must be round, floor, or ceil."

    base = price_dec.to_integral_value(rounding=ROUND_FLOOR)
    candidate = base + ending_dec

    if mode_key == "floor":
        if candidate > price_dec:
            candidate -= Decimal("1")
        if candidate < Decimal("0"):
            return None, "Ending is higher than price for floor mode."
    elif mode_key == "ceil":
        if candidate < price_dec:
            candidate += Decimal("1")
    else:
        alt = candidate + Decimal("1") if candidate < price_dec else candidate - Decimal("1")
        if alt >= Decimal("0"):
            if abs(price_dec - alt) < abs(price_dec - candidate):
                candidate = alt

    return {
        "price": _quantize(price_dec, decimals_int),
        "ending": _quantize(ending_dec, decimals_int),
        "mode": mode_key,
        "result": _quantize(candidate, decimals_int),
        "delta": _quantize(candidate - price_dec, decimals_int),
    }, None
