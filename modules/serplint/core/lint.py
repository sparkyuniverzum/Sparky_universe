from __future__ import annotations

from typing import Any, Dict, List, Tuple

TITLE_MIN = 30
TITLE_MAX = 60
TITLE_PX_MIN = 285
TITLE_PX_MAX = 580

DESC_MIN = 70
DESC_MAX = 160
DESC_PX_MIN = 430
DESC_PX_MAX = 920

WIDE = {"W", "M"}
SEMI_WIDE = {"w", "m"}


def _estimate_pixels(text: str) -> int:
    total = 0
    for char in text:
        if char in WIDE:
            total += 10
        elif char in SEMI_WIDE:
            total += 9
        elif char.isupper():
            total += 8
        elif char.islower():
            total += 7
        elif char.isdigit():
            total += 7
        elif char.isspace():
            total += 3
        else:
            total += 4
    return total


def _check_value(
    label: str,
    value: str,
    min_chars: int,
    max_chars: int,
    min_px: int,
    max_px: int,
) -> Tuple[Dict[str, int | str], List[str]]:
    length = len(value)
    pixels = _estimate_pixels(value)
    warnings: List[str] = []

    if length < min_chars:
        warnings.append(f"{label} is shorter than recommended.")
    if length > max_chars:
        warnings.append(f"{label} is longer than recommended.")
    if pixels < min_px:
        warnings.append(f"{label} may be too short in SERP width.")
    if pixels > max_px:
        warnings.append(f"{label} may be too long in SERP width.")

    return {
        "value": value,
        "length": length,
        "pixels": pixels,
    }, warnings


def lint_serp(
    title: Any,
    description: Any,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if title is None or str(title).strip() == "":
        return None, "Title is required."
    if description is None or str(description).strip() == "":
        return None, "Description is required."

    title_value = str(title).strip()
    desc_value = str(description).strip()

    issues: List[str] = []
    warnings: List[str] = []

    title_data, title_warn = _check_value(
        "Title",
        title_value,
        TITLE_MIN,
        TITLE_MAX,
        TITLE_PX_MIN,
        TITLE_PX_MAX,
    )
    desc_data, desc_warn = _check_value(
        "Description",
        desc_value,
        DESC_MIN,
        DESC_MAX,
        DESC_PX_MIN,
        DESC_PX_MAX,
    )

    warnings.extend(title_warn)
    warnings.extend(desc_warn)

    return {
        "title": title_data,
        "description": desc_data,
        "issues": issues,
        "warnings": warnings,
    }, None
