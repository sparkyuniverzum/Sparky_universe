from __future__ import annotations

import re
from typing import Any, Dict, Tuple

WORD_RE = re.compile(r"\S+")
SENTENCE_END = {".", "!", "?"}


def _last_sentence_index(text: str, min_index: int) -> int:
    for idx in range(len(text) - 1, min_index - 1, -1):
        if text[idx] in SENTENCE_END:
            return idx + 1
    return -1


def _truncate_chars(text: str, limit: int, prefer_sentence: bool) -> str:
    snippet = text[:limit]
    cut = len(snippet)
    if prefer_sentence:
        sentence_idx = _last_sentence_index(snippet, int(limit * 0.6))
        if sentence_idx != -1:
            cut = sentence_idx
    if cut == len(snippet):
        last_space = snippet.rfind(" ")
        if last_space >= int(limit * 0.6):
            cut = last_space
    return snippet[:cut].rstrip()


def _truncate_words(text: str, limit: int, prefer_sentence: bool) -> str:
    words = WORD_RE.findall(text)
    snippet = " ".join(words[:limit])
    if not prefer_sentence:
        return snippet.rstrip()
    sentence_idx = _last_sentence_index(snippet, int(len(snippet) * 0.6))
    if sentence_idx != -1:
        return snippet[:sentence_idx].rstrip()
    return snippet.rstrip()


def smart_truncate(
    text: str | None,
    *,
    limit: int,
    unit: str = "chars",
    add_ellipsis: bool = True,
    prefer_sentence: bool = True,
) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None, "Upload a file or paste text."

    if limit <= 0:
        return None, "Limit must be a positive number."

    words = WORD_RE.findall(cleaned)
    word_count = len(words)
    char_count = len(cleaned)

    if unit == "words":
        if word_count <= limit:
            output = cleaned
        else:
            output = _truncate_words(cleaned, limit, prefer_sentence)
    else:
        if char_count <= limit:
            output = cleaned
        else:
            output = _truncate_chars(cleaned, limit, prefer_sentence)

    truncated = output != cleaned
    if truncated and add_ellipsis and output and output[-1] not in SENTENCE_END:
        output = f"{output}..."

    return {
        "unit": unit,
        "limit": limit,
        "truncated": truncated,
        "original_length": {"chars": char_count, "words": word_count},
        "output_length": {
            "chars": len(output),
            "words": len(WORD_RE.findall(output)),
        },
        "output": output,
    }, None
