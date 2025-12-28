from __future__ import annotations

import secrets
from typing import Any, Dict, List, Tuple

LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?/"

MAX_COUNT = 500
MAX_LENGTH = 256


def _parse_int(value: Any, *, label: str, default: int | None = None) -> Tuple[int | None, str | None]:
    if value is None or str(value).strip() == "":
        if default is None:
            return None, f"{label} is required."
        return default, None
    raw = str(value).strip()
    try:
        number = int(raw)
    except ValueError:
        return None, f"{label} must be a whole number."
    return number, None


def _build_charset(
    *,
    use_lower: bool,
    use_upper: bool,
    use_digits: bool,
    use_symbols: bool,
    custom: str | None,
) -> str:
    charset = ""
    if use_lower:
        charset += LOWER
    if use_upper:
        charset += UPPER
    if use_digits:
        charset += DIGITS
    if use_symbols:
        charset += SYMBOLS
    if custom:
        charset += custom
    return charset


def generate_strings(
    length: Any,
    count: Any,
    *,
    use_lower: bool = True,
    use_upper: bool = False,
    use_digits: bool = True,
    use_symbols: bool = False,
    custom: str | None = None,
) -> Tuple[Dict[str, List[str]] | None, str | None]:
    length_int, error = _parse_int(length, label="Length", default=16)
    if error or length_int is None:
        return None, error

    count_int, error = _parse_int(count, label="Count", default=10)
    if error or count_int is None:
        return None, error

    if length_int <= 0 or length_int > MAX_LENGTH:
        return None, f"Length must be between 1 and {MAX_LENGTH}."
    if count_int <= 0 or count_int > MAX_COUNT:
        return None, f"Count must be between 1 and {MAX_COUNT}."

    charset = _build_charset(
        use_lower=use_lower,
        use_upper=use_upper,
        use_digits=use_digits,
        use_symbols=use_symbols,
        custom=custom,
    )
    if not charset:
        return None, "Select at least one character set."

    values = ["".join(secrets.choice(charset) for _ in range(length_int)) for _ in range(count_int)]

    return {
        "count": count_int,
        "length": length_int,
        "values": values,
    }, None
