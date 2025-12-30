from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

WORD_RE = re.compile(r"[A-Za-z0-9']+")
SENTENCE_RE = re.compile(r"[.!?]+")
VOWEL_GROUPS = re.compile(r"[aeiouy]+", re.IGNORECASE)


def _count_syllables(word: str) -> int:
    word = word.lower().strip()
    if not word:
        return 0
    groups = VOWEL_GROUPS.findall(word)
    count = len(groups)
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def readability_check(text: str | None) -> Tuple[Dict[str, Any] | None, str | None]:
    if not text or not text.strip():
        return None, "Provide text to analyze."

    cleaned = text.strip()
    words = WORD_RE.findall(cleaned)
    word_count = len(words)
    sentences = SENTENCE_RE.findall(cleaned)
    sentence_count = max(1, len(sentences))
    syllables = sum(_count_syllables(word) for word in words)

    avg_sentence_length = round(word_count / sentence_count, 2) if sentence_count else 0
    avg_word_length = round(
        sum(len(word) for word in words) / word_count, 2
    ) if word_count else 0
    avg_syllables = round(syllables / word_count, 2) if word_count else 0

    flesch = round(
        206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllables / word_count),
        1,
    )

    if flesch >= 70:
        label = "easy"
    elif flesch >= 50:
        label = "standard"
    else:
        label = "hard"

    warnings: List[str] = []
    if avg_sentence_length > 20:
        warnings.append("Average sentence length is high; consider shorter sentences.")
    if avg_syllables > 1.7:
        warnings.append("Words are complex; consider simpler wording.")
    if flesch < 50:
        warnings.append("Overall readability is low.")

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "syllable_count": syllables,
        "avg_sentence_length": avg_sentence_length,
        "avg_word_length": avg_word_length,
        "avg_syllables_per_word": avg_syllables,
        "flesch_score": flesch,
        "label": label,
        "warnings": warnings,
    }, None
