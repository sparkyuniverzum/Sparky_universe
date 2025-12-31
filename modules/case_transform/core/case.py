from __future__ import annotations

import re
from typing import Dict, List, Tuple


WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _split_words(text: str) -> List[str]:
    if not text or not text.strip():
        return []

    value = text.strip()
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", value)
    value = re.sub(r"([A-Za-z])([0-9])", r"\1 \2", value)
    value = re.sub(r"([0-9])([A-Za-z])", r"\1 \2", value)
    value = re.sub(r"[^A-Za-z0-9]+", " ", value)

    return [match.group(0) for match in WORD_RE.finditer(value)]


def _titleize(word: str) -> str:
    if not word:
        return ""
    lower = word.lower()
    return lower[0].upper() + lower[1:]


def transform_cases(text: str | None) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None or not text.strip():
        return None, "Text is required."

    words = _split_words(text)
    if not words:
        return None, "Text has no usable words."

    words_lower = [word.lower() for word in words]
    sentence = " ".join(words_lower)
    sentence = sentence[:1].upper() + sentence[1:] if sentence else ""

    title = " ".join(_titleize(word) for word in words_lower)
    camel = "".join(
        [words_lower[0]] + [_titleize(word) for word in words_lower[1:]]
    )
    pascal = "".join(_titleize(word) for word in words_lower)

    return {
        "words": words,
        "word_count": len(words),
        "lower": " ".join(words_lower),
        "upper": " ".join(words_lower).upper(),
        "title": title,
        "sentence": sentence,
        "snake": "_".join(words_lower),
        "kebab": "-".join(words_lower),
        "camel": camel,
        "pascal": pascal,
    }, None
