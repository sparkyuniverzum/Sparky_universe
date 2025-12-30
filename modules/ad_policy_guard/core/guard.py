from __future__ import annotations

from typing import Any, Dict, List, Tuple

GENERAL_PHRASES = {
    "guaranteed",
    "risk-free",
    "no risk",
    "instant approval",
    "limited time",
    "act now",
    "best price",
    "miracle",
}

FINANCE_PHRASES = {
    "guaranteed returns",
    "risk-free returns",
    "double your money",
    "get rich",
    "no credit check",
    "instant loan",
    "debt erased",
}

HEALTH_PHRASES = {
    "cure",
    "treats",
    "diagnose",
    "no side effects",
    "lose weight fast",
    "guaranteed results",
    "miracle",
}


def _pick_phrases(category: str) -> List[str]:
    if category == "finance":
        return sorted(GENERAL_PHRASES | FINANCE_PHRASES)
    if category == "health":
        return sorted(GENERAL_PHRASES | HEALTH_PHRASES)
    return sorted(GENERAL_PHRASES)


def guard_copy(text: str | None, *, category: str | None = None) -> Tuple[Dict[str, Any] | None, str | None]:
    if not text or not text.strip():
        return None, "Provide ad copy to scan."

    category = (category or "general").strip().lower()
    scan_text = text.strip()
    lower = scan_text.lower()

    phrases = _pick_phrases(category)
    hits: List[str] = []
    for phrase in phrases:
        if phrase in lower:
            hits.append(phrase)

    severity = "low"
    if hits:
        if category in {"finance", "health"}:
            severity = "high"
        else:
            severity = "medium"

    return {
        "category": category,
        "copy": scan_text,
        "flags": hits,
        "severity": severity,
        "flag_count": len(hits),
    }, None
