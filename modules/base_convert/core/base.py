from __future__ import annotations

from typing import Dict, Tuple


DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _parse_base(value: object, *, label: str) -> Tuple[int | None, str | None]:
    if value is None:
        return None, f"{label} is required."
    raw = str(value).strip()
    if not raw:
        return None, f"{label} is required."
    try:
        base = int(raw)
    except ValueError:
        return None, f"{label} must be a number."
    if base < 2 or base > 36:
        return None, f"{label} must be between 2 and 36."
    return base, None


def _strip_prefix(value: str, base: int) -> str:
    if base == 16 and value.lower().startswith("0x"):
        return value[2:]
    if base == 2 and value.lower().startswith("0b"):
        return value[2:]
    if base == 8 and value.lower().startswith("0o"):
        return value[2:]
    return value


def _parse_number(value: object, base: int) -> Tuple[int | None, str | None]:
    if value is None:
        return None, "Value is required."
    raw = str(value).strip().replace(" ", "").replace("_", "")
    if not raw:
        return None, "Value is required."

    sign = -1 if raw.startswith("-") else 1
    if raw[0] in "+-":
        raw = raw[1:]

    raw = _strip_prefix(raw, base).upper()
    if not raw:
        return None, "Value is required."

    allowed = set(DIGITS[:base])
    for char in raw:
        if char not in allowed:
            return None, f"Invalid digit for base {base}: {char}"

    return sign * int(raw, base), None


def _to_base(value: int, base: int) -> str:
    if value == 0:
        return "0"

    sign = "-" if value < 0 else ""
    value = abs(value)
    digits = []
    while value > 0:
        value, remainder = divmod(value, base)
        digits.append(DIGITS[remainder])
    return sign + "".join(reversed(digits))


def convert_base(
    value: object, base_from: object, base_to: object
) -> Tuple[Dict[str, object] | None, str | None]:
    from_base, error = _parse_base(base_from, label="From base")
    if error or from_base is None:
        return None, error

    to_base, error = _parse_base(base_to, label="To base")
    if error or to_base is None:
        return None, error

    number, error = _parse_number(value, from_base)
    if error or number is None:
        return None, error

    converted = _to_base(number, to_base)
    return {
        "input": str(value).strip(),
        "base_from": from_base,
        "base_to": to_base,
        "decimal": str(number),
        "converted": converted,
    }, None
