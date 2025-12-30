from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

WORD_RE = re.compile(r"[A-Za-z0-9']+")

BENEFIT_WORDS = {
    "save",
    "boost",
    "grow",
    "increase",
    "improve",
    "free",
    "faster",
    "easy",
    "simple",
    "proven",
    "learn",
    "discover",
    "unlock",
    "maximize",
    "reduce",
    "win",
    "better",
    "new",
}

POSITIVE_WORDS = {
    "best",
    "bright",
    "clear",
    "confident",
    "easy",
    "fast",
    "free",
    "fresh",
    "gain",
    "grow",
    "happy",
    "improve",
    "love",
    "powerful",
    "simple",
    "smart",
    "strong",
    "win",
}

NEGATIVE_WORDS = {
    "avoid",
    "bad",
    "broken",
    "fail",
    "hard",
    "lost",
    "never",
    "no",
    "pain",
    "slow",
    "stop",
    "worse",
    "risk",
}


def _words(text: str) -> List[str]:
    return WORD_RE.findall(text)


def score_headline(headline: str | None) -> Tuple[Dict[str, Any] | None, str | None]:
    if not headline or not headline.strip():
        return None, "Provide a headline to score."

    text = headline.strip()
    length = len(text)
    words = _words(text)
    word_count = len(words)
    avg_word_len = round(
        sum(len(word) for word in words) / word_count, 2
    ) if word_count else 0.0

    ideal_min = 40
    ideal_max = 60
    if length < ideal_min:
        length_points = max(0, 30 - (ideal_min - length))
    elif length > ideal_max:
        length_points = max(0, 30 - (length - ideal_max))
    else:
        length_points = 30

    if 4 <= word_count <= 10:
        clarity_points = 15
    elif 3 <= word_count <= 12:
        clarity_points = 10
    else:
        clarity_points = 5

    if avg_word_len <= 7:
        clarity_points += 10
    elif avg_word_len <= 9:
        clarity_points += 6
    else:
        clarity_points += 3

    clarity_points = min(25, clarity_points)

    lower_words = [word.lower() for word in words]
    benefit_hits = sorted({word for word in lower_words if word in BENEFIT_WORDS})
    if len(benefit_hits) >= 3:
        benefit_points = 25
    elif len(benefit_hits) == 2:
        benefit_points = 18
    elif len(benefit_hits) == 1:
        benefit_points = 10
    else:
        benefit_points = 0

    positive_hits = [word for word in lower_words if word in POSITIVE_WORDS]
    negative_hits = [word for word in lower_words if word in NEGATIVE_WORDS]
    if len(positive_hits) > len(negative_hits):
        sentiment_points = 20
        sentiment_label = "positive"
    elif len(positive_hits) == len(negative_hits):
        sentiment_points = 10
        sentiment_label = "neutral"
    else:
        sentiment_points = 5
        sentiment_label = "negative"

    total = length_points + clarity_points + benefit_points + sentiment_points
    if total >= 80:
        label = "strong"
    elif total >= 60:
        label = "solid"
    elif total >= 40:
        label = "needs work"
    else:
        label = "weak"

    suggestions: List[str] = []
    if length < ideal_min:
        suggestions.append("Headline feels short; add detail or benefit.")
    if length > ideal_max:
        suggestions.append("Headline is long; trim to the core idea.")
    if not benefit_hits:
        suggestions.append("Add a benefit cue (save, grow, improve).")
    if sentiment_label == "negative":
        suggestions.append("Try a more positive or empowering tone.")
    if word_count > 12:
        suggestions.append("Reduce word count for clarity.")

    return {
        "headline": text,
        "length": length,
        "word_count": word_count,
        "avg_word_length": avg_word_len,
        "score": total,
        "label": label,
        "components": {
            "length": length_points,
            "clarity": clarity_points,
            "benefit": benefit_points,
            "sentiment": sentiment_points,
        },
        "benefit_words": benefit_hits,
        "positive_words": sorted(set(positive_hits)),
        "negative_words": sorted(set(negative_hits)),
        "sentiment": sentiment_label,
        "suggestions": suggestions,
    }, None
