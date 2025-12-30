from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

WORD_RE = re.compile(r"[A-Za-z0-9']+")

POWER_WORDS = {
    "save",
    "boost",
    "new",
    "proven",
    "instant",
    "fast",
    "easy",
    "free",
    "exclusive",
    "limited",
    "today",
    "unlock",
    "discover",
}

SPAM_WORDS = {
    "guaranteed",
    "winner",
    "congratulations",
    "urgent",
    "act",
    "now",
    "buy",
    "cash",
    "credit",
    "prize",
    "risk-free",
    "deal",
}

SPAM_PHRASES = [
    "act now",
    "buy now",
    "click here",
    "limited time",
    "get rich",
    "no risk",
    "risk-free",
]

EMOJI_RANGES = [
    (0x1F300, 0x1F5FF),
    (0x1F600, 0x1F64F),
    (0x1F680, 0x1F6FF),
    (0x1F900, 0x1F9FF),
    (0x2600, 0x26FF),
]


def _words(text: str) -> List[str]:
    return WORD_RE.findall(text)


def _emoji_count(text: str) -> int:
    count = 0
    for char in text:
        code = ord(char)
        for start, end in EMOJI_RANGES:
            if start <= code <= end:
                count += 1
                break
    return count


def score_subject(subject: str | None) -> Tuple[Dict[str, Any] | None, str | None]:
    if not subject or not subject.strip():
        return None, "Provide a subject line."

    text = subject.strip()
    length = len(text)
    words = _words(text)
    word_count = len(words)
    avg_word_len = round(
        sum(len(word) for word in words) / word_count, 2
    ) if word_count else 0.0

    ideal_min = 30
    ideal_max = 55
    if length < ideal_min:
        length_points = max(0, 30 - (ideal_min - length))
    elif length > ideal_max:
        length_points = max(0, 30 - (length - ideal_max))
    else:
        length_points = 30

    if 4 <= word_count <= 9:
        clarity_points = 20
    elif 3 <= word_count <= 12:
        clarity_points = 14
    else:
        clarity_points = 8

    if avg_word_len <= 6:
        clarity_points += 5
    elif avg_word_len <= 8:
        clarity_points += 3
    else:
        clarity_points += 1

    clarity_points = min(25, clarity_points)

    lowered = text.lower()
    lower_words = [word.lower() for word in words]
    power_hits = sorted({word for word in lower_words if word in POWER_WORDS})
    power_points = min(15, len(power_hits) * 5)

    emoji_count = _emoji_count(text)
    if emoji_count == 1:
        emoji_points = 5
    elif emoji_count == 2:
        emoji_points = 3
    elif emoji_count > 2:
        emoji_points = 1
    else:
        emoji_points = 0

    spam_hits = sorted({word for word in lower_words if word in SPAM_WORDS})
    phrase_hits = [phrase for phrase in SPAM_PHRASES if phrase in lowered]
    spam_penalty = min(30, (len(spam_hits) + len(phrase_hits)) * 10)

    score = length_points + clarity_points + power_points + emoji_points - spam_penalty
    score = max(0, min(100, score))

    if score >= 80:
        label = "strong"
    elif score >= 60:
        label = "solid"
    elif score >= 40:
        label = "needs work"
    else:
        label = "weak"

    suggestions: List[str] = []
    if length < ideal_min:
        suggestions.append("Add more detail to reach 30-55 characters.")
    if length > ideal_max:
        suggestions.append("Trim the line to stay under 55 characters.")
    if not power_hits:
        suggestions.append("Include a benefit or power word (save, boost, new).")
    if spam_hits or phrase_hits:
        suggestions.append("Remove spammy words or phrases.")
    if word_count > 12:
        suggestions.append("Reduce word count for clarity.")
    if emoji_count > 2:
        suggestions.append("Limit emojis to one for better deliverability.")

    return {
        "subject": text,
        "length": length,
        "word_count": word_count,
        "avg_word_length": avg_word_len,
        "score": score,
        "label": label,
        "components": {
            "length": length_points,
            "clarity": clarity_points,
            "power": power_points,
            "emoji": emoji_points,
            "spam_penalty": spam_penalty,
        },
        "power_words": power_hits,
        "spam_words": spam_hits,
        "spam_phrases": phrase_hits,
        "emoji_count": emoji_count,
        "suggestions": suggestions,
    }, None
