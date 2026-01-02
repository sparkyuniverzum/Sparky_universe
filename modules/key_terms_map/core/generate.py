from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Tuple

STOPWORDS = {
    "the",
    "and",
    "that",
    "with",
    "this",
    "from",
    "into",
    "when",
    "then",
    "than",
    "over",
    "your",
    "you",
    "their",
    "there",
    "these",
    "those",
    "were",
    "been",
    "have",
    "has",
    "had",
    "will",
    "would",
    "should",
    "could",
    "what",
    "which",
    "who",
    "whom",
    "because",
    "while",
    "where",
    "about",
    "above",
    "below",
    "more",
    "most",
    "such",
    "each",
    "other",
    "very",
    "some",
    "many",
    "much",
    "also",
    "only",
    "same",
    "both",
    "between",
    "within",
    "without",
    "into",
    "just",
    "like",
    "make",
    "made",
    "makes",
    "using",
    "used",
    "use",
    "able",
    "based",
    "per",
    "via",
}


def _split_sentences(text: str) -> List[str]:
    cleaned = text.replace("\r", " ").strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def _extract_terms(text: str) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-']{3,}", text.lower())
    return [word for word in words if word not in STOPWORDS]


def build_terms_map(
    text: str | None, limit: int
) -> Tuple[Dict[str, Any] | None, str | None]:
    if text is None or not str(text).strip():
        return None, "Text is required."
    if limit <= 0 or limit > 20:
        return None, "Limit must be between 1 and 20."

    text_value = str(text)
    sentences = _split_sentences(text_value)
    if not sentences:
        return None, "Text is required."

    terms = _extract_terms(text_value)
    if not terms:
        return None, "No key terms found."

    counts = Counter(terms)
    top_terms = [term for term, _ in counts.most_common(limit)]

    items: List[Dict[str, str]] = []
    for term in top_terms:
        explanation = ""
        for sentence in sentences:
            if re.search(rf"\b{re.escape(term)}\b", sentence, re.IGNORECASE):
                explanation = sentence
                break
        items.append({"term": term, "explanation": explanation})

    return {
        "count": len(items),
        "terms": items,
    }, None
