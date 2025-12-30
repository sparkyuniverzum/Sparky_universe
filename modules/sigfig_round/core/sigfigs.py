from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, Tuple


def _parse_decimal(value: object) -> Tuple[Decimal | None, str | None]:
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


def round_sigfigs(
    value: object, sigfigs: object
) -> Tuple[Dict[str, object] | None, str | None]:
    number, error = _parse_decimal(value)
    if error or number is None:
        return None, error

    if sigfigs is None:
        return None, "Significant figures are required."
    try:
        sigfigs_int = int(str(sigfigs).strip())
    except ValueError:
        return None, "Significant figures must be a whole number."
    if sigfigs_int < 1 or sigfigs_int > 12:
        return None, "Significant figures must be between 1 and 12."

    if number == 0:
        rounded = Decimal(0)
    else:
        exp = number.adjusted()
        quant = Decimal("1").scaleb(exp - sigfigs_int + 1)
        rounded = number.quantize(quant, rounding=ROUND_HALF_UP)

    return {
        "value": str(number),
        "sigfigs": sigfigs_int,
        "rounded": str(rounded),
        "scientific": format(rounded.normalize(), "E"),
    }, None
