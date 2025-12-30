from __future__ import annotations

import math
from decimal import Decimal, InvalidOperation
from typing import Dict, Tuple


def _parse_int(value: object, *, label: str) -> Tuple[int | None, str | None]:
    if value is None:
        return None, f"{label} is required."
    raw = str(value).strip()
    if not raw:
        return None, f"{label} is required."
    compact = raw.replace(" ", "")
    try:
        return int(compact), None
    except ValueError:
        return None, f"{label} must be a whole number."


def _decimal_string(numerator: int, denominator: int) -> str:
    try:
        return str(Decimal(numerator) / Decimal(denominator))
    except (InvalidOperation, ZeroDivisionError):
        return "0"


def reduce_fraction(
    numerator: object, denominator: object
) -> Tuple[Dict[str, object] | None, str | None]:
    num, error = _parse_int(numerator, label="Numerator")
    if error or num is None:
        return None, error
    den, error = _parse_int(denominator, label="Denominator")
    if error or den is None:
        return None, error

    if den == 0:
        return None, "Denominator must not be zero."

    sign = -1 if num * den < 0 else 1
    num_abs = abs(num)
    den_abs = abs(den)
    divisor = math.gcd(num_abs, den_abs)
    simple_num = num_abs // divisor
    simple_den = den_abs // divisor
    simple_num *= sign

    if simple_den < 0:
        simple_num = -simple_num
        simple_den = abs(simple_den)

    whole = abs(simple_num) // simple_den
    remainder = abs(simple_num) % simple_den
    mixed: str
    if remainder == 0:
        mixed = str(simple_num // simple_den)
    elif whole == 0:
        mixed = f"{'-' if simple_num < 0 else ''}{remainder}/{simple_den}"
    else:
        sign_prefix = "-" if simple_num < 0 else ""
        mixed = f"{sign_prefix}{whole} {remainder}/{simple_den}"

    return {
        "numerator": simple_num,
        "denominator": simple_den,
        "simplified": f"{simple_num}/{simple_den}",
        "decimal": _decimal_string(simple_num, simple_den),
        "mixed": mixed,
        "remainder": remainder,
    }, None
