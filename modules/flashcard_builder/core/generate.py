
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
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
COLON_LINE = re.compile(r"^\s*([^:]{2,60})\s*:\s*(.+)$")
DASH_LINE = re.compile(r"^\s*([^\-]{2,60})\s*-\s*(.+)$")


def _split_sentences(text: str) -> List[str]:
    cleaned = text.replace("\r", " ").strip()
    if not cleaned:
        return []
    parts = SENTENCE_SPLIT.split(cleaned)
    return [part.strip() for part in parts if part.strip()]


def _extract_terms(text: str) -> List[str]:
    words = [word.lower() for word in WORD_RE.findall(text)]
    return [word for word in words if len(word) >= 4 and word not in STOPWORDS]


def build_flashcards(
    text: str | None,
    limit: int,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if text is None or not str(text).strip():
        return None, "Text is required."
    if limit <= 0 or limit > 20:
        return None, "Limit must be between 1 and 20."

    text_value = str(text)
    cards: List[Dict[str, str]] = []
    for line in text_value.splitlines():
        line = line.strip()
        if not line:
            continue
        match = COLON_LINE.match(line) or DASH_LINE.match(line)
        if match:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if term and definition:
                cards.append({"question": term, "answer": definition})
        if len(cards) >= limit:
            break

    if len(cards) < limit:
        sentences = _split_sentences(text_value)
        terms = _extract_terms(text_value)
        counts = Counter(terms)
        for term, _ in counts.most_common():
            if len(cards) >= limit:
                break
            sentence = ""
            for line in sentences:
                if re.search(rf"{re.escape(term)}", line, re.IGNORECASE):
                    sentence = line
                    break
            if sentence:
                cards.append({"question": f"What is {term}?", "answer": sentence})

    return {"count": len(cards), "cards": cards}, None
