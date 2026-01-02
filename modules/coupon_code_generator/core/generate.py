from __future__ import annotations

import secrets
from typing import Any, Dict, List, Tuple

CHARSETS = {
    "alnum": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    "alpha": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "numeric": "0123456789",
    "base32": "ABCDEFGHJKLMNPQRSTUVWXYZ23456789",
}


def _clean_prefix(value: str | None) -> str:
    if not value:
        return ""
    cleaned = value.strip().upper().replace(" ", "")
    return cleaned


def _group_code(code: str, group_size: int, separator: str) -> str:
    if group_size <= 0:
        return code
    groups = [code[idx : idx + group_size] for idx in range(0, len(code), group_size)]
    return separator.join(groups)


def _check_digit(code: str, alphabet: str) -> str:
    total = 0
    for ch in code:
        total += alphabet.index(ch)
    return alphabet[total % len(alphabet)]


def generate_codes(
    *,
    prefix: str | None,
    count: int,
    length: int,
    charset: str,
    add_check: bool,
    group_size: int | None,
    separator: str,
) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned_prefix = _clean_prefix(prefix)
    if count <= 0 or count > 5000:
        return None, "Count must be between 1 and 5000."
    if length <= 0 or length > 64:
        return None, "Length must be between 1 and 64."

    alphabet = CHARSETS.get(charset, CHARSETS["alnum"])
    group_size = group_size or 0

    codes: List[str] = []
    seen: set[str] = set()
    attempts = 0
    max_attempts = count * 10

    while len(codes) < count and attempts < max_attempts:
        attempts += 1
        raw = "".join(secrets.choice(alphabet) for _ in range(length))
        if add_check:
            raw = raw + _check_digit(raw, alphabet)
        if group_size > 0:
            raw = _group_code(raw, group_size, separator)
        code = raw
        if cleaned_prefix:
            code = f"{cleaned_prefix}{separator}{raw}"
        if code in seen:
            continue
        seen.add(code)
        codes.append(code)

    if len(codes) < count:
        return None, "Could not generate enough unique codes."

    return {
        "count": len(codes),
        "prefix": cleaned_prefix,
        "length": length,
        "charset": charset,
        "add_check_digit": add_check,
        "group_size": group_size or None,
        "separator": separator,
        "codes": codes,
    }, None
