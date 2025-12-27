from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Tuple


def _parse_decimal(value: Any, *, label: str) -> Tuple[Decimal | None, str | None]:
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
        return None, "Invalid number format."


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def _scale_to_int(value: Decimal, decimals: int) -> int:
    scaled = value.scaleb(decimals)
    return int(scaled.to_integral_value())


def simplify_ratio(
    left: Any,
    right: Any,
    *,
    decimals: int = 6,
) -> Tuple[Dict[str, str] | None, str | None]:
    left_dec, error = _parse_decimal(left, label="Left")
    if error or left_dec is None:
        return None, error

    right_dec, error = _parse_decimal(right, label="Right")
    if error or right_dec is None:
        return None, error

    if left_dec == Decimal("0") and right_dec == Decimal("0"):
        return None, "Both values cannot be zero."

    decimals = max(0, min(int(decimals), 8))

    left_scaled = _scale_to_int(left_dec, decimals)
    right_scaled = _scale_to_int(right_dec, decimals)

    if left_scaled == 0 and right_scaled == 0:
        return None, "Ratio too small to simplify."

    divisor = _gcd(left_scaled, right_scaled)
    simplified_left = left_scaled // divisor if divisor else left_scaled
    simplified_right = right_scaled // divisor if divisor else right_scaled

    return {
        "left": str(left_dec),
        "right": str(right_dec),
        "simplified_left": str(simplified_left),
        "simplified_right": str(simplified_right),
        "ratio": f"{simplified_left}:{simplified_right}",
    }, None
