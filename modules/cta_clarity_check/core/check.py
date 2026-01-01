from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

WORD_RE = re.compile(r"[A-Za-z0-9']+")
SENTENCE_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")

ACTION_VERBS = {
    "get",
    "start",
    "try",
    "download",
    "book",
    "request",
    "contact",
    "buy",
    "subscribe",
    "join",
    "learn",
    "explore",
    "sign",
    "save",
    "claim",
    "upgrade",
    "schedule",
    "register",
    "apply",
}

CTA_PHRASES = [
    "get started",
    "sign up",
    "learn more",
    "book a demo",
    "request a demo",
    "start free",
    "try it",
    "join now",
    "contact us",
    "buy now",
    "subscribe",
    "download",
    "schedule a call",
]

CTA_HINTS = [
    "free",
    "demo",
    "trial",
    "quote",
    "pricing",
]


def _words(text: str) -> List[str]:
    return WORD_RE.findall(text)


def _split_sentences(text: str) -> List[str]:
    return [sentence.strip() for sentence in SENTENCE_RE.findall(text) if sentence.strip()]


def _candidate_from_line(line: str) -> bool:
    lowered = line.lower()
    if any(phrase in lowered for phrase in CTA_PHRASES):
        return True
    words = _words(lowered)
    return bool(words) and words[0] in ACTION_VERBS


def _find_candidates(text: str) -> List[str]:
    candidates: List[str] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        if _candidate_from_line(line):
            candidates.append(line)
    if candidates:
        return candidates[:3]

    for sentence in _split_sentences(text):
        if _candidate_from_line(sentence):
            candidates.append(sentence)
        if len(candidates) >= 3:
            break
    return candidates[:3]


def cta_clarity_check(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None, "Paste text to analyze."

    candidates = _find_candidates(cleaned)
    has_cta = bool(candidates)
    primary = candidates[0] if candidates else ""
    primary_words = _words(primary)
    word_count = len(primary_words)
    starts_with_verb = bool(primary_words) and primary_words[0].lower() in ACTION_VERBS

    score = 0
    if has_cta:
        score += 40
    if starts_with_verb:
        score += 30
    if 1 < word_count <= 6:
        score += 20
    if any(hint in primary.lower() for hint in CTA_HINTS):
        score += 10

    issues: List[str] = []
    warnings: List[str] = []

    if not has_cta:
        issues.append("CTA not found.")
    else:
        if word_count <= 1:
            warnings.append("CTA looks too vague; add a clear action.")
        if word_count > 6:
            warnings.append("CTA is long; shorten to 2-6 words.")
        if not starts_with_verb:
            warnings.append("CTA should start with an action verb.")

    if not has_cta:
        verdict = "missing"
    elif score >= 80:
        verdict = "clear"
    elif score >= 60:
        verdict = "ok"
    else:
        verdict = "unclear"

    return {
        "verdict": verdict,
        "score": score,
        "primary_cta": primary,
        "cta_candidates": candidates,
        "word_count": word_count,
        "starts_with_verb": starts_with_verb,
        "issues": issues,
        "warnings": warnings,
    }, None
