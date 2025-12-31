from __future__ import annotations

import re
import unicodedata
from typing import Dict, Tuple


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def clean_text(
    text: str | None,
    *,
    trim: bool = True,
    collapse_spaces: bool = True,
    remove_empty_lines: bool = False,
    strip_accents: bool = False,
    to_lower: bool = False,
) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None:
        return None, "Text is required."

    original = text
    value = text

    if strip_accents:
        value = _strip_accents(value)

    if to_lower:
        value = value.lower()

    lines = value.splitlines()
    cleaned_lines = []
    for line in lines:
        line_value = line
        if trim:
            line_value = line_value.strip()
        if collapse_spaces:
            line_value = re.sub(r"[ \t]+", " ", line_value)
        if remove_empty_lines and not line_value:
            continue
        cleaned_lines.append(line_value)

    value = "\n".join(cleaned_lines)

    if trim:
        value = value.strip()

    return {
        "original_length": len(original),
        "cleaned_length": len(value),
        "removed_chars": len(original) - len(value),
        "cleaned": value,
    }, None
