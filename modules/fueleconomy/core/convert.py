from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Tuple

L_PER_GAL_US = Decimal("3.785411784")
L_PER_GAL_UK = Decimal("4.54609")
KM_PER_MILE = Decimal("1.609344")
HUNDRED = Decimal("100")

MILES_PER_100KM = HUNDRED / KM_PER_MILE
MPG_US_FACTOR = MILES_PER_100KM * L_PER_GAL_US
MPG_UK_FACTOR = MILES_PER_100KM * L_PER_GAL_UK

UNITS: Dict[str, Dict[str, str]] = {
    "l_per_100km": {"label": "L/100 km"},
    "mpg_us": {"label": "MPG (US)"},
    "mpg_uk": {"label": "MPG (UK)"},
}


def list_units() -> Dict[str, Dict[str, str]]:
    return {key: {"label": str(meta["label"])} for key, meta in UNITS.items()}


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


def _quantize(value: Decimal, decimals: int = 2) -> str:
    decimals = max(0, min(int(decimals), 6))
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def _to_l_per_100km(value: Decimal, unit: str) -> Decimal:
    if unit == "l_per_100km":
        return value
    if unit == "mpg_us":
        return MPG_US_FACTOR / value
    if unit == "mpg_uk":
        return MPG_UK_FACTOR / value
    raise ValueError("Unknown unit.")


def _from_l_per_100km(value: Decimal, unit: str) -> Decimal:
    if unit == "l_per_100km":
        return value
    if unit == "mpg_us":
        return MPG_US_FACTOR / value
    if unit == "mpg_uk":
        return MPG_UK_FACTOR / value
    raise ValueError("Unknown unit.")


def convert_fuel_economy(
    value: Any,
    from_unit: str,
    to_unit: str,
    *,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    if from_unit not in UNITS or to_unit not in UNITS:
        return None, "Unknown unit."

    value_dec, error = _parse_decimal(value)
    if error or value_dec is None:
        return None, error

    if value_dec <= Decimal("0"):
        return None, "Value must be greater than zero."

    base_value = _to_l_per_100km(value_dec, from_unit)
    result_value = _from_l_per_100km(base_value, to_unit)

    return {
        "value": _quantize(value_dec, decimals),
        "result": _quantize(result_value, decimals),
        "from_unit": from_unit,
        "to_unit": to_unit,
    }, None
