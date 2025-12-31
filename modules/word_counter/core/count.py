from __future__ import annotations

import math
import re
from typing import Dict, Tuple


WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")
SENTENCE_RE = re.compile(r"[.!?]+")


def count_text(text: str | None, *, wpm: int = 200) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None or not text.strip():
        return None, "Text is required."

    words = WORD_RE.findall(text)
    word_count = len(words)
    sentence_count = len(SENTENCE_RE.findall(text))
    if sentence_count == 0 and word_count:
        sentence_count = 1

    lines = text.splitlines()
    line_count = len(lines)
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    paragraph_count = len(paragraphs)

    char_count = len(text)
    char_no_space = len(re.sub(r"\s+", "", text))

    minutes = math.ceil(word_count / wpm) if word_count else 0

    return {
        "words": word_count,
        "characters": char_count,
        "characters_no_space": char_no_space,
        "sentences": sentence_count,
        "lines": line_count,
        "paragraphs": paragraph_count,
        "reading_minutes": minutes,
        "wpm": wpm,
    }, None
