from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

REQUIRED = {
    "goal": [
        "goal",
        "objective",
        "aim",
        "purpose",
        "kpi",
        "outcome",
        "target",
    ],
    "audience": [
        "audience",
        "persona",
        "target audience",
        "customer",
        "user",
        "segment",
        "reader",
    ],
    "tone": [
        "tone",
        "voice",
        "style",
        "formal",
        "informal",
        "friendly",
        "professional",
        "brand voice",
    ],
    "length": [
        "length",
        "word count",
        "words",
        "characters",
        "char",
        "duration",
        "minutes",
        "secs",
        "pages",
    ],
    "cta": [
        "cta",
        "call to action",
        "action",
        "sign up",
        "subscribe",
        "buy",
        "download",
        "book",
        "contact",
        "get started",
        "learn more",
    ],
}

LENGTH_HINTS = [
    "word",
    "words",
    "character",
    "characters",
    "minute",
    "minutes",
    "sec",
    "secs",
    "page",
    "pages",
]


def _hits(text: str, keywords: List[str]) -> List[str]:
    hits: List[str] = []
    for keyword in keywords:
        if keyword in text:
            hits.append(keyword)
    return hits


def _has_length_hint(text: str) -> bool:
    if re.search(r"\b\d+\b", text) and any(hint in text for hint in LENGTH_HINTS):
        return True
    return False


def brief_completeness(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None, "Paste a brief to analyze."

    lowered = cleaned.lower()
    present: Dict[str, bool] = {}
    signals: Dict[str, List[str]] = {}
    missing: List[str] = []

    for key, keywords in REQUIRED.items():
        hits = _hits(lowered, keywords)
        if key == "length" and not hits and _has_length_hint(lowered):
            hits = ["numeric length"]
        signals[key] = hits
        present[key] = bool(hits)
        if not hits:
            missing.append(key)

    total = len(REQUIRED)
    present_count = total - len(missing)
    score = round((present_count / total) * 100) if total else 0
    checklist = [{"item": key, "ok": present[key]} for key in REQUIRED.keys()]

    return {
        "score": score,
        "summary": {"present": present_count, "total": total},
        "present": present,
        "missing": missing,
        "checklist": checklist,
        "signals": signals,
    }, None
