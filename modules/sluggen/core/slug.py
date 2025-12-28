from __future__ import annotations

import re
from typing import Any, Dict, Tuple


RE_NON_ALNUM = re.compile(r"[^a-z0-9]+")
RE_DASH = re.compile(r"-+")

TRANSLIT_MAP = {
    "á": "a",
    "č": "c",
    "ď": "d",
    "é": "e",
    "ě": "e",
    "í": "i",
    "ň": "n",
    "ó": "o",
    "ř": "r",
    "š": "s",
    "ť": "t",
    "ú": "u",
    "ů": "u",
    "ý": "y",
    "ž": "z",
}


def _transliterate(text: str) -> str:
    return "".join(TRANSLIT_MAP.get(ch, ch) for ch in text)


def generate_slug(
    text: Any,
    *,
    delimiter: str = "-",
    lowercase: bool = True,
    remove_accents: bool = True,
) -> Tuple[Dict[str, str] | None, str | None]:
    if text is None:
        return None, "Text is required."
    raw = str(text).strip()
    if not raw:
        return None, "Text is required."

    cleaned = raw
    if remove_accents:
        cleaned = _transliterate(cleaned)

    cleaned = cleaned.lower() if lowercase else cleaned
    cleaned = RE_NON_ALNUM.sub(delimiter, cleaned)
    cleaned = RE_DASH.sub(delimiter, cleaned).strip(delimiter)

    return {
        "source": raw,
        "slug": cleaned,
    }, None
