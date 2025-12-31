from __future__ import annotations

import re
from typing import Dict, Tuple


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
CARD_RE = re.compile(r"(?:\d[ -]?){13,19}")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _mask_generic(value: str) -> str:
    value = value.strip()
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


def _mask_email(value: str) -> str:
    local, _, domain = value.partition("@")
    if not domain:
        return _mask_generic(value)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + ("*" * (len(local) - 2)) + local[-1]
    return f"{masked_local}@{domain}"


def _mask_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) <= 2:
        return "*" * len(digits)
    return "*" * (len(digits) - 2) + digits[-2:]


def _mask_card(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) <= 4:
        return "*" * len(digits)
    return "*" * (len(digits) - 4) + digits[-4:]


def _mask_iban(value: str) -> str:
    cleaned = re.sub(r"\s+", "", value).upper()
    if len(cleaned) <= 8:
        return "*" * len(cleaned)
    return cleaned[:4] + ("*" * (len(cleaned) - 8)) + cleaned[-4:]


def _mask_ip(value: str) -> str:
    parts = value.strip().split(".")
    if len(parts) != 4:
        return _mask_generic(value)
    return ".".join(parts[:3] + ["***"])


def _luhn_check(value: str) -> bool:
    digits = [int(ch) for ch in value if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    reverse = list(reversed(digits))
    for idx, digit in enumerate(reverse):
        if idx % 2 == 1:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return total % 10 == 0


def _iban_check(value: str) -> bool:
    cleaned = re.sub(r"\s+", "", value).upper()
    if not IBAN_RE.fullmatch(cleaned):
        return False
    rearranged = cleaned[4:] + cleaned[:4]
    digits = ""
    for ch in rearranged:
        if ch.isdigit():
            digits += ch
        elif "A" <= ch <= "Z":
            digits += str(ord(ch) - 55)
        else:
            return False
    remainder = 0
    for ch in digits:
        remainder = (remainder * 10 + int(ch)) % 97
    return remainder == 1


def _valid_ip(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def redact_text(
    text: str | None,
    *,
    redact_email: bool = True,
    redact_phone: bool = True,
    redact_iban: bool = True,
    redact_card: bool = True,
    redact_ip: bool = True,
) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None or not text.strip():
        return None, "Text is required."

    result = text
    counts = {"email": 0, "phone": 0, "iban": 0, "card": 0, "ip": 0}

    if redact_email:
        def mask_email(match: re.Match[str]) -> str:
            counts["email"] += 1
            return _mask_email(match.group(0))

        result = EMAIL_RE.sub(mask_email, result)

    if redact_phone:
        def mask_phone(match: re.Match[str]) -> str:
            digits = re.sub(r"\D", "", match.group(0))
            if not (7 <= len(digits) <= 15):
                return match.group(0)
            counts["phone"] += 1
            return _mask_phone(match.group(0))

        result = PHONE_RE.sub(mask_phone, result)

    if redact_iban:
        def mask_iban(match: re.Match[str]) -> str:
            value = match.group(0)
            if not _iban_check(value):
                return value
            counts["iban"] += 1
            return _mask_iban(value)

        result = IBAN_RE.sub(mask_iban, result)

    if redact_card:
        def mask_card(match: re.Match[str]) -> str:
            value = match.group(0)
            digits = re.sub(r"\D", "", value)
            if not _luhn_check(digits):
                return value
            counts["card"] += 1
            return _mask_card(value)

        result = CARD_RE.sub(mask_card, result)

    if redact_ip:
        def mask_ip(match: re.Match[str]) -> str:
            value = match.group(0)
            if not _valid_ip(value):
                return value
            counts["ip"] += 1
            return _mask_ip(value)

        result = IP_RE.sub(mask_ip, result)

    return {
        "counts": counts,
        "total": sum(counts.values()),
        "result": result,
    }, None
