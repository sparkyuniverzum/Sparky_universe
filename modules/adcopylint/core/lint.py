from __future__ import annotations

from typing import Any, Dict, List, Tuple

LIMITS = {
    "google_headline": {"label": "Google headline", "limit": 30},
    "google_description": {"label": "Google description", "limit": 90},
    "meta_primary": {"label": "Meta primary text", "limit": 125},
    "meta_headline": {"label": "Meta headline", "limit": 40},
    "meta_description": {"label": "Meta description", "limit": 30},
    "linkedin_intro": {"label": "LinkedIn intro", "limit": 150},
    "linkedin_headline": {"label": "LinkedIn headline", "limit": 70},
}


def _parse_kind(value: Any) -> Tuple[str | None, str | None]:
    if value is None:
        return "google_headline", None
    raw = str(value).strip()
    if not raw:
        return "google_headline", None
    if raw not in LIMITS:
        return None, "Unknown ad copy type."
    return raw, None


def lint_ad_copy(
    kind: Any,
    text: Any,
) -> Tuple[Dict[str, Any] | None, str | None]:
    kind_value, error = _parse_kind(kind)
    if error or kind_value is None:
        return None, error

    if text is None:
        return None, "Provide at least one line of copy."
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    if not lines:
        return None, "Provide at least one line of copy."

    limit = LIMITS[kind_value]["limit"]
    label = LIMITS[kind_value]["label"]

    items: List[Dict[str, Any]] = []
    over = 0
    for line in lines:
        length = len(line)
        ok = length <= limit
        if not ok:
            over += 1
        items.append(
            {
                "text": line,
                "length": length,
                "ok": ok,
                "remaining": limit - length,
            }
        )

    return {
        "kind": kind_value,
        "label": label,
        "limit": limit,
        "total": len(lines),
        "over": over,
        "items": items,
    }, None
