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

WORD_RE = re.compile(r"[A-Za-z0-9']+")


def headline_body_alignment(
    headline: str | None,
    body: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    headline = (headline or "").strip()
    body = (body or "").strip()
    if not headline:
        return None, "Provide a headline."
    if not body:
        return None, "Provide body text."

    keywords = [
        word.lower()
        for word in WORD_RE.findall(headline)
        if len(word) >= 4 and word.lower() not in STOPWORDS
    ]
    if not keywords:
        return None, "Headline is too short to analyze."

    body_lower = body.lower()
    matches = [word for word in keywords if word in body_lower]
    missing = [word for word in keywords if word not in body_lower]
    score = round((len(matches) / len(keywords)) * 100, 1)
    verdict = "aligned" if score >= 70 else "weak"

    return {
        "score": score,
        "verdict": verdict,
        "keywords": keywords,
        "matches": matches,
        "missing": missing,
    }, None
