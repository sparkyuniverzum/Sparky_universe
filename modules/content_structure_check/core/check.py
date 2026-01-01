from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

SENTENCE_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")

CONCLUSION_HINTS = [
    "in short",
    "in summary",
    "summary",
    "to conclude",
    "in conclusion",
    "next steps",
    "next",
    "thanks",
    "thank you",
    "cta",
]


def _split_paragraphs(text: str) -> List[str]:
    parts = re.split(r"\n\s*\n", text.strip())
    return [part.strip() for part in parts if part.strip()]


def _split_sentences(text: str) -> List[str]:
    return [sentence.strip() for sentence in SENTENCE_RE.findall(text) if sentence.strip()]


def _detect_headings(lines: List[str]) -> List[str]:
    headings: List[str] = []
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned.startswith("#"):
            headings.append(cleaned.lstrip("#").strip())
            continue
        if cleaned.endswith(":") and len(cleaned) <= 60:
            headings.append(cleaned[:-1].strip())
            continue
        if cleaned.isupper() and 4 <= len(cleaned) <= 60:
            headings.append(cleaned)
    return headings


def _has_conclusion_hint(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in CONCLUSION_HINTS)


def structure_check(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None, "Paste text to analyze."

    paragraphs = _split_paragraphs(cleaned)
    sentences = _split_sentences(cleaned)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    headings = _detect_headings(lines)

    intro_ok = bool(paragraphs)
    body_ok = len(paragraphs) >= 2
    outro_ok = False
    if len(paragraphs) >= 2:
        last_para = paragraphs[-1]
        outro_ok = _has_conclusion_hint(last_para) or len(last_para) >= 60

    long_paragraphs: List[int] = []
    for idx, para in enumerate(paragraphs, start=1):
        para_sentences = _split_sentences(para)
        if len(para) > 800 or len(para_sentences) > 6:
            long_paragraphs.append(idx)

    issues: List[str] = []
    warnings: List[str] = []

    if not intro_ok:
        issues.append("Missing intro paragraph.")
    if not body_ok:
        issues.append("Add body paragraphs to develop the topic.")
    if not outro_ok:
        issues.append("Add a closing paragraph or CTA.")
    if not headings:
        warnings.append("Add headings to improve scanning.")
    if long_paragraphs:
        warnings.append(f"Long paragraphs detected: {', '.join(map(str, long_paragraphs))}.")

    return {
        "paragraph_count": len(paragraphs),
        "sentence_count": len(sentences),
        "heading_count": len(headings),
        "headings": headings[:6],
        "long_paragraphs": long_paragraphs,
        "checks": {
            "intro": intro_ok,
            "body": body_ok,
            "outro": outro_ok,
            "headings": bool(headings),
        },
        "issues": issues,
        "warnings": warnings,
    }, None
