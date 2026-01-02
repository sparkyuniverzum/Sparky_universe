from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "this",
    "from",
    "your",
    "you",
    "are",
    "was",
    "were",
    "have",
    "has",
    "had",
    "will",
    "would",
    "should",
    "could",
    "into",
    "about",
    "after",
    "before",
    "under",
    "over",
    "between",
    "their",
    "there",
    "then",
    "than",
    "also",
    "some",
    "such",
    "each",
    "more",
    "most",
    "other",
    "when",
    "where",
    "what",
    "which",
    "while",
    "because",
    "only",
    "just",
    "like",
}

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
WORD_RE = re.compile(r"[A-Za-z0-9']+")


def _tokenize(sentence: str) -> set[str]:
    words = [word.lower() for word in WORD_RE.findall(sentence)]
    return {word for word in words if len(word) > 2 and word not in STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def redundancy_scan(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    text = (text or "").strip()
    if not text:
        return None, "Provide text to analyze."

    raw_sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    sentences = [s for s in raw_sentences if len(s) >= 30][:80]
    token_sets = [_tokenize(sentence) for sentence in sentences]

    pairs: List[Dict[str, Any]] = []
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            similarity = _jaccard(token_sets[i], token_sets[j])
            if similarity >= 0.75:
                pairs.append(
                    {
                        "sentence_a": sentences[i],
                        "sentence_b": sentences[j],
                        "similarity": round(similarity, 2),
                    }
                )

    pairs = sorted(pairs, key=lambda item: item["similarity"], reverse=True)[:15]

    return {"pairs": pairs, "pair_count": len(pairs)}, None
