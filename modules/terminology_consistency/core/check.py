from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Tuple

TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*")
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
    "into",
    "onto",
}


def _normalize(token: str) -> str:
    return re.sub(r"[-_]", "", token.lower())


def terminology_consistency(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    text = (text or "").strip()
    if not text:
        return None, "Provide text to analyze."

    variants: Dict[str, Counter[str]] = {}
    for token in TOKEN_RE.findall(text):
        norm = _normalize(token)
        if len(norm) < 3:
            continue
        if norm.isdigit() or norm in STOPWORDS:
            continue
        variants.setdefault(norm, Counter())[token] += 1

    issues: List[Dict[str, Any]] = []
    for norm, counter in sorted(variants.items()):
        if len(counter) < 2:
            continue
        preferred, _ = counter.most_common(1)[0]
        issues.append(
            {
                "normalized": norm,
                "preferred": preferred,
                "total": sum(counter.values()),
                "variants": [
                    {"term": term, "count": count}
                    for term, count in counter.most_common()
                ],
            }
        )

    return {"issues": issues, "issue_count": len(issues)}, None
