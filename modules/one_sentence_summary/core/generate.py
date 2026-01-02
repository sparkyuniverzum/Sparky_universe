
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

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
WORD_RE = re.compile(r"[A-Za-z0-9']+")


def _split_sentences(text: str) -> List[str]:
    cleaned = text.replace("\r", " ").strip()
    if not cleaned:
        return []
    parts = SENTENCE_SPLIT.split(cleaned)
    return [part.strip() for part in parts if part.strip()]


def _extract_terms(text: str) -> List[str]:
    words = [word.lower() for word in WORD_RE.findall(text)]
    return [word for word in words if len(word) >= 4 and word not in STOPWORDS]


def one_sentence_summary(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if text is None or not str(text).strip():
        return None, "Text is required."

    text_value = str(text)
    sentences = _split_sentences(text_value)
    if not sentences:
        return None, "Text is required."

    terms = _extract_terms(text_value)
    if not terms:
        return {"summary": sentences[0], "keyword": ""}, None

    counts = Counter(terms)

    def score(sentence: str) -> int:
        return sum(counts.get(term, 0) for term in _extract_terms(sentence))

    scored = [(score(sentence), idx, sentence) for idx, sentence in enumerate(sentences)]
    scored.sort(key=lambda item: (-item[0], item[1]))
    summary = scored[0][2]
    keyword = counts.most_common(1)[0][0]

    return {
        "summary": summary,
        "keyword": keyword,
    }, None
