from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

WORD_RE = re.compile(r"[A-Za-z0-9']+")

FRIENDLY_MARKERS = {
    "hey",
    "thanks",
    "awesome",
    "excited",
    "love",
    "great",
    "glad",
    "friendly",
    "cheers",
}

PRO_MARKERS = {
    "regarding",
    "please",
    "sincerely",
    "summary",
    "update",
    "agenda",
    "attached",
    "meeting",
    "request",
    "confirm",
}

INFORMAL_MARKERS = {
    "lol",
    "btw",
    "omg",
    "gonna",
    "kinda",
    "wanna",
}

HARD_NEGATIVES = {
    "hate",
    "stupid",
    "idiot",
    "worst",
    "never",
}


def _words(text: str) -> List[str]:
    return WORD_RE.findall(text)


def _score(words: List[str], markers: set[str]) -> int:
    return sum(1 for word in words if word in markers)


def guard_tone(
    text: str | None,
    *,
    target: str | None = None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if not text or not text.strip():
        return None, "Provide text to analyze."

    target = (target or "auto").strip().lower()
    if target not in {"auto", "friendly", "professional", "neutral"}:
        target = "auto"

    cleaned = text.strip()
    words = [word.lower() for word in _words(cleaned)]

    friendly_score = _score(words, FRIENDLY_MARKERS)
    pro_score = _score(words, PRO_MARKERS)
    informal_hits = sorted({word for word in words if word in INFORMAL_MARKERS})
    negative_hits = sorted({word for word in words if word in HARD_NEGATIVES})

    tone_scores = {
        "friendly": friendly_score,
        "professional": pro_score,
        "neutral": max(0, len(words) - friendly_score - pro_score),
    }

    detected = max(tone_scores, key=tone_scores.get)
    confidence = tone_scores[detected] if tone_scores else 0

    issues: List[str] = []
    warnings: List[str] = []

    if informal_hits:
        warnings.append(f"Informal markers found: {', '.join(informal_hits)}.")
    if negative_hits:
        issues.append(f"Negative tone markers: {', '.join(negative_hits)}.")

    if target != "auto" and detected != target:
        warnings.append(f"Detected tone is {detected}, target is {target}.")

    if detected == "friendly" and pro_score > 0:
        warnings.append("Mixed friendly and professional signals.")
    if detected == "professional" and friendly_score > 0:
        warnings.append("Mixed professional and friendly signals.")

    return {
        "text_length": len(cleaned),
        "word_count": len(words),
        "target": target,
        "detected": detected,
        "confidence": confidence,
        "scores": tone_scores,
        "informal_markers": informal_hits,
        "negative_markers": negative_hits,
        "issues": issues,
        "warnings": warnings,
    }, None
