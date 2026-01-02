from __future__ import annotations

from typing import Any, Dict, Tuple

ASCII_QUOTES = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u00ab": '"',
    "\u00bb": '"',
}

ASCII_DASHES = {
    "\u2013": "-",
    "\u2014": "-",
    "\u2212": "-",
}


def _to_ascii(text: str) -> Tuple[str, int, int]:
    quote_changes = 0
    dash_changes = 0
    for src, dest in ASCII_QUOTES.items():
        if src in text:
            quote_changes += text.count(src)
            text = text.replace(src, dest)
    for src, dest in ASCII_DASHES.items():
        if src in text:
            dash_changes += text.count(src)
            text = text.replace(src, dest)
    return text, quote_changes, dash_changes


def _to_typographic(text: str) -> Tuple[str, int, int]:
    dash_changes = 0
    if "---" in text:
        dash_changes += text.count("---")
        text = text.replace("---", "\u2014")
    if "--" in text:
        dash_changes += text.count("--")
        text = text.replace("--", "\u2014")
    if " - " in text:
        dash_changes += text.count(" - ")
        text = text.replace(" - ", " \u2013 ")

    result = []
    double_open = True
    single_open = True
    quote_changes = 0

    for idx, ch in enumerate(text):
        if ch == '"':
            result.append("\u201c" if double_open else "\u201d")
            double_open = not double_open
            quote_changes += 1
            continue
        if ch == "'":
            prev = text[idx - 1] if idx > 0 else ""
            next_ch = text[idx + 1] if idx + 1 < len(text) else ""
            if prev.isalnum() and next_ch.isalnum():
                result.append("\u2019")
            else:
                result.append("\u2018" if single_open else "\u2019")
                single_open = not single_open
            quote_changes += 1
            continue
        result.append(ch)

    return "".join(result), quote_changes, dash_changes


def normalize_quotes_dashes(
    text: str | None,
    *,
    mode: str = "ascii",
) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None, "Upload a file or paste text."

    normalized = cleaned
    quote_changes = 0
    dash_changes = 0

    if mode == "typographic":
        normalized, quote_changes, dash_changes = _to_typographic(cleaned)
    else:
        normalized, quote_changes, dash_changes = _to_ascii(cleaned)

    return {
        "mode": mode,
        "quote_changes": quote_changes,
        "dash_changes": dash_changes,
        "output": normalized,
    }, None
