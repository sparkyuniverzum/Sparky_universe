from __future__ import annotations

import secrets
from typing import Any, Dict, List, Tuple

DEFAULT_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-"
MAX_COUNT = 1000
MAX_LENGTH = 128
MAX_ALPHABET = 128


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


def _parse_alphabet(value: Any) -> Tuple[str | None, str | None]:
    if value is None:
        return DEFAULT_ALPHABET, None
    raw = str(value)
    if raw.strip() == "":
        return DEFAULT_ALPHABET, None
    alphabet = raw.strip()
    if len(alphabet) < 2:
        return None, "Alphabet must contain at least 2 characters."
    if len(alphabet) > MAX_ALPHABET:
        return None, f"Alphabet must be {MAX_ALPHABET} characters or less."
    return alphabet, None


def generate_nanoids(
    length: Any,
    count: Any,
    *,
    alphabet: Any = None,
) -> Tuple[Dict[str, List[str]] | None, str | None]:
    length_int, error = _parse_int(length, label="Length", default=12)
    if error or length_int is None:
        return None, error

    count_int, error = _parse_int(count, label="Count", default=10)
    if error or count_int is None:
        return None, error

    if length_int <= 0 or length_int > MAX_LENGTH:
        return None, f"Length must be between 1 and {MAX_LENGTH}."
    if count_int <= 0 or count_int > MAX_COUNT:
        return None, f"Count must be between 1 and {MAX_COUNT}."

    alphabet_value, error = _parse_alphabet(alphabet)
    if error or alphabet_value is None:
        return None, error

    values = [
        "".join(secrets.choice(alphabet_value) for _ in range(length_int))
        for _ in range(count_int)
    ]

    return {
        "count": count_int,
        "length": length_int,
        "alphabet_length": len(alphabet_value),
        "values": values,
    }, None
