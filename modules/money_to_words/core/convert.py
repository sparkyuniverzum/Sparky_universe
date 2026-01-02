from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple

EN_ONES = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]
EN_TEENS = [
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]
EN_TENS = [
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
]
EN_SCALES = [
    (1_000_000_000, "billion"),
    (1_000_000, "million"),
    (1_000, "thousand"),
]

CS_ONES_MASC = [
    "nula",
    "jeden",
    "dva",
    "tři",
    "čtyři",
    "pět",
    "šest",
    "sedm",
    "osm",
    "devět",
]
CS_ONES_FEM = [
    "nula",
    "jedna",
    "dvě",
    "tři",
    "čtyři",
    "pět",
    "šest",
    "sedm",
    "osm",
    "devět",
]
CS_TEENS = [
    "deset",
    "jedenáct",
    "dvanáct",
    "třináct",
    "čtrnáct",
    "patnáct",
    "šestnáct",
    "sedmnáct",
    "osmnáct",
    "devatenáct",
]
CS_TENS = [
    "",
    "",
    "dvacet",
    "třicet",
    "čtyřicet",
    "padesát",
    "šedesát",
    "sedmdesát",
    "osmdesát",
    "devadesát",
]
CS_HUNDREDS = {
    1: "sto",
    2: "dvě stě",
    3: "tři sta",
    4: "čtyři sta",
    5: "pět set",
    6: "šest set",
    7: "sedm set",
    8: "osm set",
    9: "devět set",
}
CS_SCALES = [
    (1_000_000_000, ("miliarda", "miliardy", "miliard"), CS_ONES_FEM),
    (1_000_000, ("milion", "miliony", "milionů"), CS_ONES_MASC),
    (1_000, ("tisíc", "tisíce", "tisíc"), CS_ONES_MASC),
]


def _clean_amount(raw: str) -> str:
    trimmed = raw.strip().replace(" ", "")
    if "," in trimmed and "." in trimmed:
        trimmed = trimmed.replace(",", "")
    elif "," in trimmed:
        trimmed = trimmed.replace(",", ".")
    return trimmed


def _parse_amount(value: str | None) -> Tuple[Decimal | None, str | None]:
    if not value or not value.strip():
        return None, "Enter an amount."
    try:
        cleaned = _clean_amount(value)
        amount = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None, "Amount must be a number."
    return amount, None


def _en_under_1000(value: int) -> List[str]:
    parts: List[str] = []
    hundreds = value // 100
    remainder = value % 100
    if hundreds:
        parts.append(EN_ONES[hundreds])
        parts.append("hundred")
    if remainder >= 20:
        tens = remainder // 10
        ones = remainder % 10
        parts.append(EN_TENS[tens])
        if ones:
            parts.append(EN_ONES[ones])
    elif remainder >= 10:
        parts.append(EN_TEENS[remainder - 10])
    elif remainder > 0:
        parts.append(EN_ONES[remainder])
    return parts


def _cs_under_1000(value: int, ones: List[str]) -> List[str]:
    parts: List[str] = []
    hundreds = value // 100
    remainder = value % 100
    if hundreds:
        parts.append(CS_HUNDREDS.get(hundreds, ""))
    if remainder >= 20:
        tens = remainder // 10
        ones = remainder % 10
        parts.append(CS_TENS[tens])
        if ones:
            parts.append(CS_ONES[ones])
    elif remainder >= 10:
        parts.append(CS_TEENS[remainder - 10])
    elif remainder > 0:
        parts.append(ones[remainder])
    return [part for part in parts if part]


def _en_number(value: int) -> str:
    if value == 0:
        return EN_ONES[0]
    parts: List[str] = []
    remaining = value
    for scale_value, scale_name in EN_SCALES:
        if remaining >= scale_value:
            chunk = remaining // scale_value
            remaining = remaining % scale_value
            parts.extend(_en_under_1000(chunk))
            parts.append(scale_name)
    if remaining:
        parts.extend(_en_under_1000(remaining))
    return " ".join(part for part in parts if part)


def _cs_number(value: int, ones: List[str]) -> str:
    if value == 0:
        return ones[0]
    parts: List[str] = []
    remaining = value
    for scale_value, scale_forms, scale_ones in CS_SCALES:
        if remaining >= scale_value:
            chunk = remaining // scale_value
            remaining = remaining % scale_value
            parts.extend(_cs_under_1000(chunk, scale_ones))
            parts.append(_cs_choose_form(chunk, scale_forms))
    if remaining:
        parts.extend(_cs_under_1000(remaining, ones))
    return " ".join(part for part in parts if part)


def _cs_label_forms(label: str | None, defaults: Tuple[str, str, str]) -> Tuple[str, str, str]:
    if label and "|" in label:
        parts = [part.strip() for part in label.split("|")]
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
    if label:
        return label, label, label
    return defaults


def _cs_choose_form(value: int, forms: Tuple[str, str, str]) -> str:
    mod100 = value % 100
    mod10 = value % 10
    if 11 <= mod100 <= 14:
        return forms[2]
    if mod10 == 1:
        return forms[0]
    if mod10 in {2, 3, 4}:
        return forms[1]
    return forms[2]


def money_to_words(
    amount_raw: str | None,
    *,
    language: str = "en",
    major_label: str | None = None,
    minor_label: str | None = None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    amount, error = _parse_amount(amount_raw)
    if error:
        return None, error
    assert amount is not None

    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    major = int(amount)
    minor = int((amount - Decimal(major)) * 100)

    if major < 0:
        return None, "Amount must be positive."
    if major > 999_999_999:
        return None, "Amount is too large."

    language = (language or "en").lower().strip()
    if language not in {"en", "cs"}:
        return None, "Language must be en or cs."

    if language == "cs":
        major_words = _cs_number(major, CS_ONES_FEM)
        minor_words = _cs_number(minor, CS_ONES_MASC)
        major_forms = _cs_label_forms(major_label, ("koruna", "koruny", "korun"))
        minor_forms = _cs_label_forms(minor_label, ("haléř", "haléře", "haléřů"))
        major_label = _cs_choose_form(major, major_forms)
        minor_label = _cs_choose_form(minor, minor_forms)
    else:
        major_words = _en_number(major)
        minor_words = _en_number(minor)
        major_label = major_label or "dollars"
        minor_label = minor_label or "cents"

    full = f"{major_words} {major_label}"
    connector = " a " if language == "cs" else " and "
    full += f"{connector}{minor_words} {minor_label}"

    return {
        "amount": str(amount),
        "language": language,
        "major": major,
        "minor": minor,
        "major_words": major_words,
        "minor_words": minor_words,
        "output": full,
    }, None
