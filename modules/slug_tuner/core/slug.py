from __future__ import annotations

import re
import unicodedata
from typing import Dict, Tuple


DEFAULT_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _normalize_separators(text: str, sep: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", sep, text)
    text = re.sub(rf"{re.escape(sep)}+", sep, text)
    return text.strip(sep)


def tune_slug(
    text: str | None,
    *,
    separator: str = "-",
    max_length: object = None,
    lowercase: bool = True,
    strip_accents: bool = True,
    remove_stop_words: bool = False,
    custom_stop_words: str | None = None,
) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None or not text.strip():
        return None, "Text is required."

    sep = separator or "-"
    if sep not in {"-", "_"}:
        return None, "Separator must be '-' or '_'."

    value = text.strip()
    if strip_accents:
        value = _strip_accents(value)
    if lowercase:
        value = value.lower()

    tokens = _normalize_separators(value, sep).split(sep) if value else []

    stop_words = set(DEFAULT_STOP_WORDS)
    if custom_stop_words:
        stop_words.update(
            word.strip().lower()
            for word in custom_stop_words.split(",")
            if word.strip()
        )

    if remove_stop_words:
        tokens = [token for token in tokens if token not in stop_words]

    slug = sep.join(token for token in tokens if token)

    if max_length is not None and str(max_length).strip():
        try:
            max_len = int(str(max_length).strip())
        except ValueError:
            return None, "Max length must be a whole number."
        if max_len < 1:
            return None, "Max length must be at least 1."
        slug = slug[:max_len].rstrip(sep)

    return {
        "slug": slug,
        "length": len(slug),
        "separator": sep,
    }, None
