from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

DEFINITION_CUES = [
    " is ",
    " are ",
    " means ",
    " refers to ",
    " defined as ",
    " is called ",
    ": ",
    " — ",
]


def _split_sentences(text: str) -> List[str]:
    cleaned = text.replace("\r", " ").strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def _score_sentence(sentence: str) -> int:
    lowered = f" {sentence.lower()} "
    score = 0
    for cue in DEFINITION_CUES:
        if cue in lowered:
            score += 1
    if ":" in sentence:
        score += 1
    return score


def extract_definitions(text: str | None, limit: int) -> Tuple[Dict[str, Any] | None, str | None]:
    if text is None or not str(text).strip():
        return None, "Text is required."
    if limit <= 0 or limit > 12:
        return None, "Limit must be between 1 and 12."

    sentences = _split_sentences(str(text))
    if not sentences:
        return None, "Text is required."

    scored = [
        (idx, sentence, _score_sentence(sentence))
        for idx, sentence in enumerate(sentences)
    ]
    scored.sort(key=lambda item: (-item[2], item[0]))

    picked = [item[1] for item in scored if item[2] > 0]
    if len(picked) < limit:
        for sentence in sentences:
            if sentence not in picked:
                picked.append(sentence)
            if len(picked) >= limit:
                break

    definitions = picked[:limit]
    return {
        "count": len(definitions),
        "definitions": definitions,
    }, None
