from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Tuple

UNITS: Dict[str, Dict[str, str | Decimal]] = {
    "c": {"label": "Celsius", "factor": Decimal("1"), "offset": Decimal("273.15")},
    "f": {"label": "Fahrenheit", "factor": Decimal("0.5555555556"), "offset": Decimal("459.67")},
    "k": {"label": "Kelvin", "factor": Decimal("1"), "offset": Decimal("0")},
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


def _quantize(value: Decimal, decimals: int = 4) -> str:
    decimals = max(0, min(int(decimals), 8))
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def convert_temperature(
    value: Any,
    from_unit: str,
    to_unit: str,
    *,
    decimals: int = 4,
) -> Tuple[Dict[str, str] | None, str | None]:
    if from_unit not in UNITS or to_unit not in UNITS:
        return None, "Unknown unit."

    value_dec, error = _parse_decimal(value)
    if error or value_dec is None:
        return None, error

    from_factor = Decimal(str(UNITS[from_unit]["factor"]))
    to_factor = Decimal(str(UNITS[to_unit]["factor"]))
    from_offset = Decimal(str(UNITS[from_unit]["offset"]))
    to_offset = Decimal(str(UNITS[to_unit]["offset"]))

    base_value = (value_dec + from_offset) * from_factor
    result_value = (base_value / to_factor) - to_offset

    return {
        "value": _quantize(value_dec, decimals),
        "result": _quantize(result_value, decimals),
        "from_unit": from_unit,
        "to_unit": to_unit,
    }, None
