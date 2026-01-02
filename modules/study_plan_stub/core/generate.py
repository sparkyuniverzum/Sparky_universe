
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

WORD_RE = re.compile(r"[A-Za-z0-9']+")


def _extract_terms(text: str) -> List[str]:
    words = [word.lower() for word in WORD_RE.findall(text)]
    return [word for word in words if len(word) >= 4 and word not in STOPWORDS]


def build_study_plan(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if text is None or not str(text).strip():
        return None, "Text is required."

    terms = _extract_terms(str(text))
    if not terms:
        return None, "No key terms found."

    counts = Counter(terms)
    focus_terms = [term for term, _ in counts.most_common(4)]
    primary = focus_terms[0]
    secondary = focus_terms[1] if len(focus_terms) > 1 else primary
    tertiary = focus_terms[2] if len(focus_terms) > 2 else primary

    steps = [
        f"Skim the material and list key terms: {', '.join(focus_terms)}.",
        f"Write one-sentence definitions for {primary} and {secondary}.",
        f"Create two examples that use {primary}.",
        f"Self-test: answer five questions about {', '.join([primary, secondary, tertiary])}.",
    ]

    return {
        "focus_terms": focus_terms,
        "steps": steps,
    }, None
