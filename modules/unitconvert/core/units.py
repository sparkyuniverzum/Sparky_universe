from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Tuple


UnitSpec = Dict[str, str | Decimal]

UNITS: Dict[str, UnitSpec] = {
    # Length (base: meter)
    "m": {"domain": "length", "factor": Decimal("1"), "label": "Meter"},
    "cm": {"domain": "length", "factor": Decimal("0.01"), "label": "Centimeter"},
    "mm": {"domain": "length", "factor": Decimal("0.001"), "label": "Millimeter"},
    "km": {"domain": "length", "factor": Decimal("1000"), "label": "Kilometer"},
    "inch": {"domain": "length", "factor": Decimal("0.0254"), "label": "Inch"},
    "ft": {"domain": "length", "factor": Decimal("0.3048"), "label": "Foot"},
    "yd": {"domain": "length", "factor": Decimal("0.9144"), "label": "Yard"},
    "mi": {"domain": "length", "factor": Decimal("1609.344"), "label": "Mile"},
    # Mass (base: kilogram)
    "kg": {"domain": "mass", "factor": Decimal("1"), "label": "Kilogram"},
    "g": {"domain": "mass", "factor": Decimal("0.001"), "label": "Gram"},
    "mg": {"domain": "mass", "factor": Decimal("0.000001"), "label": "Milligram"},
    "lb": {"domain": "mass", "factor": Decimal("0.45359237"), "label": "Pound"},
    "oz": {"domain": "mass", "factor": Decimal("0.028349523125"), "label": "Ounce"},
    # Volume (base: liter)
    "l": {"domain": "volume", "factor": Decimal("1"), "label": "Liter"},
    "ml": {"domain": "volume", "factor": Decimal("0.001"), "label": "Milliliter"},
    "cl": {"domain": "volume", "factor": Decimal("0.01"), "label": "Centiliter"},
    "dl": {"domain": "volume", "factor": Decimal("0.1"), "label": "Deciliter"},
    "gal": {"domain": "volume", "factor": Decimal("3.785411784"), "label": "Gallon (US)"},
    "qt": {"domain": "volume", "factor": Decimal("0.946352946"), "label": "Quart (US)"},
    # Temperature (base: kelvin, with offset)
    "k": {"domain": "temperature", "factor": Decimal("1"), "offset": Decimal("0"), "label": "Kelvin"},
    "c": {"domain": "temperature", "factor": Decimal("1"), "offset": Decimal("273.15"), "label": "Celsius"},
    "f": {"domain": "temperature", "factor": Decimal("0.5555555556"), "offset": Decimal("459.67"), "label": "Fahrenheit"},
}


def list_units() -> Dict[str, Dict[str, str]]:
    return {
        key: {
            "label": str(spec["label"]),
            "domain": str(spec["domain"]),
        }
        for key, spec in UNITS.items()
    }


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


def _quantize(value: Decimal, decimals: int = 6) -> str:
    decimals = max(0, min(int(decimals), 12))
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def convert_value(
    value: Any,
    from_unit: str,
    to_unit: str,
    *,
    decimals: int = 6,
) -> Tuple[Dict[str, str] | None, str | None]:
    if from_unit not in UNITS or to_unit not in UNITS:
        return None, "Unknown unit."

    from_spec = UNITS[from_unit]
    to_spec = UNITS[to_unit]
    if from_spec["domain"] != to_spec["domain"]:
        return None, "Units must be in the same domain."

    value_dec, error = _parse_decimal(value)
    if error or value_dec is None:
        return None, error

    from_factor = Decimal(str(from_spec["factor"]))
    to_factor = Decimal(str(to_spec["factor"]))
    from_offset = Decimal(str(from_spec.get("offset", Decimal("0"))))
    to_offset = Decimal(str(to_spec.get("offset", Decimal("0"))))

    base_value = (value_dec + from_offset) * from_factor
    target_value = (base_value / to_factor) - to_offset

    return {
        "value": _quantize(value_dec, decimals),
        "result": _quantize(target_value, decimals),
        "from_unit": from_unit,
        "to_unit": to_unit,
        "domain": str(from_spec["domain"]),
    }, None
