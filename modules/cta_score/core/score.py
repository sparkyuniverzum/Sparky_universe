from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

WORD_RE = re.compile(r"[A-Za-z0-9']+")

ACTION_VERBS = {
    "get",
    "start",
    "try",
    "book",
    "schedule",
    "download",
    "join",
    "subscribe",
    "buy",
    "shop",
    "claim",
    "discover",
    "learn",
    "unlock",
    "save",
    "build",
    "create",
    "upgrade",
    "compare",
}

BENEFIT_WORDS = {
    "free",
    "faster",
    "better",
    "smarter",
    "easy",
    "instant",
    "bonus",
    "exclusive",
    "trial",
    "demo",
    "discount",
    "save",
    "boost",
}

URGENCY_WORDS = {
    "today",
    "now",
    "limited",
    "ends",
    "last",
    "soon",
    "final",
}

WEAK_PHRASES = [
    "click here",
    "learn more",
    "submit",
    "get started",
]


def _words(text: str) -> List[str]:
    return WORD_RE.findall(text)


def score_cta(cta: str | None) -> Tuple[Dict[str, Any] | None, str | None]:
    if not cta or not cta.strip():
        return None, "Provide a CTA phrase."

    text = cta.strip()
    words = _words(text)
    word_count = len(words)
    avg_word_len = round(
        sum(len(word) for word in words) / word_count, 2
    ) if word_count else 0.0
    lower_words = [word.lower() for word in words]
    lowered = text.lower()

    starts_with_action = bool(lower_words) and lower_words[0] in ACTION_VERBS
    contains_action = any(word in ACTION_VERBS for word in lower_words)
    action_points = 30 if starts_with_action else (12 if contains_action else 0)

    benefit_hits = sorted({word for word in lower_words if word in BENEFIT_WORDS})
    benefit_points = 20 if benefit_hits else 0

    urgency_hits = sorted({word for word in lower_words if word in URGENCY_WORDS})
    urgency_points = 15 if urgency_hits else 0

    if 2 <= word_count <= 5:
        length_points = 20
    elif word_count <= 7:
        length_points = 12
    else:
        length_points = 6

    if avg_word_len <= 6:
        clarity_points = 15
    elif avg_word_len <= 8:
        clarity_points = 10
    else:
        clarity_points = 6

    weak_hits = [phrase for phrase in WEAK_PHRASES if phrase in lowered]
    penalty = min(20, len(weak_hits) * 10)

    score = action_points + benefit_points + urgency_points + length_points + clarity_points
    score = max(0, min(100, score - penalty))

    if score >= 80:
        label = "strong"
    elif score >= 60:
        label = "solid"
    elif score >= 40:
        label = "needs work"
    else:
        label = "weak"

    suggestions: List[str] = []
    if not starts_with_action:
        suggestions.append("Start with an action verb (Get, Try, Book).")
    if not benefit_hits:
        suggestions.append("Add a benefit word (free, demo, instant).")
    if not urgency_hits:
        suggestions.append("Add urgency (today, now, limited).")
    if word_count > 7:
        suggestions.append("Shorten the CTA to 2-5 words.")
    if weak_hits:
        suggestions.append("Replace weak phrases with specific action.")

    return {
        "cta": text,
        "word_count": word_count,
        "avg_word_length": avg_word_len,
        "score": score,
        "label": label,
        "components": {
            "action": action_points,
            "benefit": benefit_points,
            "urgency": urgency_points,
            "length": length_points,
            "clarity": clarity_points,
            "penalty": penalty,
        },
        "action_hit": starts_with_action,
        "benefit_words": benefit_hits,
        "urgency_words": urgency_hits,
        "weak_phrases": weak_hits,
        "suggestions": suggestions,
    }, None
