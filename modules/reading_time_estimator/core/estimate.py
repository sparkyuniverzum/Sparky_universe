from __future__ import annotations

import re
from typing import Any, Dict, Tuple

WORD_RE = re.compile(r"[A-Za-z0-9']+")


def _format_duration(seconds: int) -> str:
    minutes = seconds // 60
    remaining = seconds % 60
    if minutes:
        return f"{minutes}m {remaining}s"
    return f"{remaining}s"


def estimate_reading_time(
    text: str | None,
    wpm: int | None = 200,
) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None, "Paste text to analyze."

    if wpm is None:
        wpm = 200
    if wpm < 80 or wpm > 500:
        return None, "WPM must be between 80 and 500."

    words = WORD_RE.findall(cleaned)
    word_count = len(words)
    if word_count == 0:
        return None, "Text has no readable words."

    char_count = len(cleaned)
    seconds = int(round((word_count / wpm) * 60))

    min_seconds = int(round((word_count / 240) * 60))
    max_seconds = int(round((word_count / 180) * 60))

    return {
        "word_count": word_count,
        "character_count": char_count,
        "wpm": wpm,
        "estimated_seconds": seconds,
        "estimated_minutes": round(seconds / 60, 2),
        "estimated_time": _format_duration(seconds),
        "range_seconds": {"min": min_seconds, "max": max_seconds},
        "range_time": {
            "min": _format_duration(min_seconds),
            "max": _format_duration(max_seconds),
        },
    }, None
