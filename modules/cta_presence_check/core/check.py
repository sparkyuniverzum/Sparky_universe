from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

PHRASES = [
    "sign up",
    "get started",
    "start now",
    "try now",
    "try it",
    "download",
    "learn more",
    "contact us",
    "buy now",
    "order now",
    "subscribe",
    "join",
    "book a call",
    "request a demo",
    "apply now",
]


def cta_presence_check(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    text = (text or "").strip()
    if not text:
        return None, "Provide text to analyze."

    matches: List[Dict[str, Any]] = []
    for phrase in PHRASES:
        pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
        found = pattern.findall(text)
        if found:
            matches.append({"phrase": phrase, "count": len(found)})

    cta_found = bool(matches)
    suggestion = "" if cta_found else "Add a clear CTA like 'Get started' or 'Contact us'."

    return {
        "cta_found": cta_found,
        "matches": matches,
        "suggestion": suggestion,
    }, None
