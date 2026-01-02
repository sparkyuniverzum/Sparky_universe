from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

PLACEHOLDER_PATTERNS = {
    "triple_curly": re.compile(r"\{\{\{\s*[^{}]+\s*\}\}\}"),
    "double_curly": re.compile(r"\{\{\s*[^{}]+\s*\}\}"),
    "dollar_brace": re.compile(r"\$\{\s*[^}]+\s*\}"),
    "percent": re.compile(r"%[A-Z0-9_]+%"),
    "bracket": re.compile(r"\[[A-Z0-9 _-]{2,}\]"),
    "angle": re.compile(r"<<[^<>]+>>"),
}


def find_placeholders(text: str | None) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None, "Upload a file or paste text."

    counts: Dict[str, int] = {}
    types: Dict[str, set[str]] = {}
    total = 0

    for name, pattern in PLACEHOLDER_PATTERNS.items():
        for match in pattern.findall(cleaned):
            placeholder = match.strip()
            total += 1
            counts[placeholder] = counts.get(placeholder, 0) + 1
            types.setdefault(placeholder, set()).add(name)

    items = [
        {
            "placeholder": placeholder,
            "count": count,
            "types": sorted(types.get(placeholder, [])),
        }
        for placeholder, count in counts.items()
    ]
    items.sort(key=lambda item: (-item["count"], item["placeholder"]))

    return {
        "total": total,
        "unique": len(items),
        "items": items,
    }, None
