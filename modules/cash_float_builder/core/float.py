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


def _parse_int(value: object, *, label: str, default: int | None = None) -> Tuple[int | None, str | None]:
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


def _parse_list(raw: object, *, label: str) -> Tuple[List[str] | None, str | None]:
    if raw is None:
        return None, f"{label} is required."
    text = str(raw).strip()
    if not text:
        return None, f"{label} is required."
    tokens = [token for token in re.split(r"[,\s]+", text) if token]
    if len(tokens) > MAX_ITEMS:
        return None, f"Too many items (limit {MAX_ITEMS})."
    return tokens, None


def build_float(
    denominations: object,
    counts: object,
    *,
    target: object = None,
    decimals: object = 2,
) -> Tuple[Dict[str, object] | None, str | None]:
    decimals_int, error = _parse_int(decimals, label="Decimals", default=2)
    if error:
        return None, error
    if decimals_int is None or decimals_int < 0 or decimals_int > 4:
        return None, "Decimals must be between 0 and 4."

    denom_tokens, error = _parse_list(denominations, label="Denominations")
    if error or denom_tokens is None:
        return None, error
    count_tokens, error = _parse_list(counts, label="Counts")
    if error or count_tokens is None:
        return None, error

    if len(denom_tokens) != len(count_tokens):
        return None, "Denominations and counts must have the same length."

    items: List[Dict[str, object]] = []
    total = Decimal("0")
    for denom_raw, count_raw in zip(denom_tokens, count_tokens):
        denom_dec, error = _parse_decimal(denom_raw, label="Denomination")
        if error or denom_dec is None:
            return None, error
        if denom_dec <= 0:
            return None, "Denominations must be positive."

        count_int, error = _parse_int(count_raw, label="Count")
        if error or count_int is None:
            return None, error
        if count_int < 0:
            return None, "Counts must be non-negative."

        line_total = denom_dec * Decimal(count_int)
        total += line_total
        items.append(
            {
                "denomination": _quantize(denom_dec, decimals_int),
                "count": count_int,
                "amount": _quantize(line_total, decimals_int),
            }
        )

    result: Dict[str, object] = {
        "total": _quantize(total, decimals_int),
        "items": items,
        "decimals": decimals_int,
    }

    if target is not None and str(target).strip():
        target_dec, error = _parse_decimal(target, label="Target")
        if error or target_dec is None:
            return None, error
        delta = total - target_dec
        result.update(
            {
                "target": _quantize(target_dec, decimals_int),
                "delta": _quantize(delta, decimals_int),
            }
        )

    return result, None
