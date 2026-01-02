from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

UNIT_GROUPS = {
    "weight": ["kg", "g", "lb", "lbs", "oz"],
    "length": ["km", "m", "cm", "mm", "in", "ft", "yd"],
    "time": ["day", "days", "hr", "hrs", "h", "min", "mins", "s", "sec", "secs"],
    "volume": ["ml", "l", "liter", "litre", "gal", "gallon"],
}

unit_to_group: Dict[str, str] = {}
for group, units in UNIT_GROUPS.items():
    for unit in units:
        unit_to_group[unit] = group

sorted_units = sorted(unit_to_group.keys(), key=len, reverse=True)
UNIT_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(" + "|".join(re.escape(u) for u in sorted_units) + r")\b",
    re.IGNORECASE,
)

CURRENCY_RE = re.compile(r"[$\u20ac\u00a3]|\b(usd|eur|gbp|czk|aud|cad)\b", re.IGNORECASE)
DECIMAL_COMMA = re.compile(r"\b\d+,\d+\b")
DECIMAL_DOT = re.compile(r"\b\d+\.\d+\b")
THOUSANDS_COMMA = re.compile(r"\b\d{1,3}(,\d{3})+\b")
THOUSANDS_DOT = re.compile(r"\b\d{1,3}(\.\d{3})+\b")
THOUSANDS_SPACE = re.compile(r"\b\d{1,3}( \d{3})+\b")


def numbers_units_consistency(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    text = (text or "").strip()
    if not text:
        return None, "Provide text to analyze."

    currencies = {match.group(0).lower() for match in CURRENCY_RE.finditer(text)}
    currency_issue = len(currencies) > 1

    number_styles = {
        "decimal_comma": bool(DECIMAL_COMMA.search(text)),
        "decimal_dot": bool(DECIMAL_DOT.search(text)),
        "thousands_comma": bool(THOUSANDS_COMMA.search(text)),
        "thousands_dot": bool(THOUSANDS_DOT.search(text)),
        "thousands_space": bool(THOUSANDS_SPACE.search(text)),
    }

    issues: List[str] = []
    if number_styles["decimal_comma"] and number_styles["decimal_dot"]:
        issues.append("Mixed decimal separators (comma and dot).")

    thousand_styles = [
        number_styles["thousands_comma"],
        number_styles["thousands_dot"],
        number_styles["thousands_space"],
    ]
    if sum(1 for style in thousand_styles if style) > 1:
        issues.append("Mixed thousand separators detected.")

    unit_seen: Dict[str, set[str]] = {group: set() for group in UNIT_GROUPS}
    for match in UNIT_RE.finditer(text):
        unit = match.group(1).lower()
        group = unit_to_group.get(unit)
        if group:
            unit_seen[group].add(unit)

    for group, units in unit_seen.items():
        if len(units) > 1:
            issues.append(
                f"Mixed {group} units: {', '.join(sorted(units))}."
            )

    if currency_issue:
        issues.append("Multiple currencies detected.")

    return {
        "currencies": sorted(currencies),
        "number_styles": number_styles,
        "unit_groups": {group: sorted(units) for group, units in unit_seen.items() if units},
        "issues": issues,
    }, None
