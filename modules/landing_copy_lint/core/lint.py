from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

WORD_RE = re.compile(r"[A-Za-z0-9']+")

BENEFIT_WORDS = {
    "save",
    "boost",
    "grow",
    "faster",
    "simpler",
    "easy",
    "reduce",
    "increase",
    "improve",
    "better",
}

PROOF_WORDS = {
    "customers",
    "teams",
    "reviews",
    "rated",
    "trusted",
    "case study",
    "testimonials",
}

RISK_WORDS = {
    "free trial",
    "money back",
    "guarantee",
    "cancel anytime",
    "no credit card",
}

ACTION_VERBS = {
    "get",
    "start",
    "try",
    "book",
    "download",
    "join",
    "request",
    "schedule",
    "buy",
}


def _words(text: str) -> List[str]:
    return WORD_RE.findall(text)


def lint_copy(
    *,
    headline: str | None,
    subheadline: str | None,
    cta: str | None,
    proof: str | None,
    risk: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    headline = (headline or "").strip()
    subheadline = (subheadline or "").strip()
    cta = (cta or "").strip()
    proof = (proof or "").strip()
    risk = (risk or "").strip()

    if not headline:
        return None, "Headline is required."

    issues: List[str] = []
    warnings: List[str] = []

    headline_len = len(headline)
    if headline_len < 15:
        warnings.append("Headline is short; add specificity.")
    if headline_len > 80:
        warnings.append("Headline is long; tighten the message.")

    combined = f"{headline} {subheadline}".lower()
    benefit_hits = [word for word in BENEFIT_WORDS if word in combined]
    benefit_ok = bool(benefit_hits)
    if not benefit_ok:
        issues.append("Missing clear benefit in headline or subheadline.")

    cta_words = [word.lower() for word in _words(cta)]
    cta_ok = bool(cta_words)
    if not cta_ok:
        issues.append("CTA is missing.")
    else:
        if cta_words[0] not in ACTION_VERBS:
            warnings.append("CTA should start with an action verb.")

    proof_lower = proof.lower()
    proof_ok = any(word in proof_lower for word in PROOF_WORDS) or bool(re.search(r"\\d", proof_lower))
    if not proof_ok:
        issues.append("Add social proof (numbers, reviews, trusted by).")

    risk_lower = risk.lower()
    risk_ok = any(phrase in risk_lower for phrase in RISK_WORDS)
    if not risk_ok:
        warnings.append("Consider adding risk reversal (free trial, cancel anytime).")

    score = 0
    score += 25 if headline else 0
    score += 25 if benefit_ok else 0
    score += 25 if cta_ok else 0
    score += 25 if proof_ok else 0
    if risk_ok:
        score += 5

    score = min(100, score)

    if score >= 80:
        label = "strong"
    elif score >= 60:
        label = "solid"
    elif score >= 40:
        label = "needs work"
    else:
        label = "weak"

    return {
        "headline": headline,
        "subheadline": subheadline,
        "cta": cta,
        "proof": proof,
        "risk": risk,
        "score": score,
        "label": label,
        "benefit_words": benefit_hits,
        "checks": {
            "headline": bool(headline),
            "benefit": benefit_ok,
            "cta": cta_ok,
            "proof": proof_ok,
            "risk": risk_ok,
        },
        "issues": issues,
        "warnings": warnings,
    }, None
