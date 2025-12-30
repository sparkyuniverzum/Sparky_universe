from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, List, Tuple


DEFAULT_DENOMS = "100,50,20,10,5,2,1,0.5,0.2,0.1,0.05,0.02,0.01"
MAX_DENOMS = 40


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


def _to_minor_units(value: Decimal, decimals: int) -> Tuple[int, str | None]:
    scale = Decimal(10) ** decimals
    scaled = value * scale
    rounded = scaled.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if rounded != scaled:
        return 0, "Amount precision exceeds selected decimals."
    return int(rounded), None


def _parse_denoms(raw: object, decimals: int) -> Tuple[List[int] | None, str | None]:
    text = DEFAULT_DENOMS if raw is None or not str(raw).strip() else str(raw)
    tokens = [token for token in re.split(r"[,\s]+", text) if token.strip()]
    if not tokens:
        return None, "Denominations are required."
    if len(tokens) > MAX_DENOMS:
        return None, f"Too many denominations (limit {MAX_DENOMS})."

    denoms: List[int] = []
    for token in tokens:
        value, error = _parse_decimal(token, label="Denomination")
        if error or value is None:
            return None, error
        if value <= 0:
            return None, "Denominations must be positive."
        units, error = _to_minor_units(value, decimals)
        if error:
            return None, error
        denoms.append(units)

    denoms = sorted(set(denoms), reverse=True)
    return denoms, None


def breakdown_amount(
    amount: object,
    denoms: object,
    *,
    decimals: object = 2,
) -> Tuple[Dict[str, object] | None, str | None]:
    amount_dec, error = _parse_decimal(amount, label="Amount")
    if error or amount_dec is None:
        return None, error

    decimals_int, error = _parse_int(decimals, label="Decimals", default=2)
    if error:
        return None, error
    if decimals_int < 0 or decimals_int > 4:
        return None, "Decimals must be between 0 and 4."

    if amount_dec < Decimal("0"):
        return None, "Amount must be non-negative."

    amount_units, error = _to_minor_units(amount_dec, decimals_int)
    if error:
        return None, error

    denoms_units, error = _parse_denoms(denoms, decimals_int)
    if error or denoms_units is None:
        return None, error

    remainder = amount_units
    breakdown: List[Dict[str, object]] = []

    for denom in denoms_units:
        if denom <= 0:
            continue
        count = remainder // denom
        if count:
            amount_units = denom * count
            breakdown.append(
                {
                    "denomination": _quantize(
                        Decimal(denom) / (Decimal(10) ** decimals_int),
                        decimals_int,
                    ),
                    "count": int(count),
                    "amount": _quantize(
                        Decimal(amount_units) / (Decimal(10) ** decimals_int),
                        decimals_int,
                    ),
                }
            )
            remainder -= amount_units

    return {
        "amount": _quantize(amount_dec, decimals_int),
        "breakdown": breakdown,
        "remainder": _quantize(
            Decimal(remainder) / (Decimal(10) ** decimals_int), decimals_int
        ),
        "decimals": decimals_int,
    }, None
