from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _split_lines(value: str | None) -> List[str]:
    if not value:
        return []
    cleaned = value.replace("\r", "").replace(",", "\n")
    return [line.strip() for line in cleaned.split("\n") if line.strip()]


def build_memory_ladder(
    items: str | None,
    must_count: int,
    should_count: int,
    topic: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    item_list = _split_lines(items)
    if not item_list:
        return None, "Items are required."
    if must_count < 0 or should_count < 0:
        return None, "Counts must be zero or higher."

    total = len(item_list)
    must_count = min(must_count, total)
    should_count = min(should_count, max(total - must_count, 0))

    must = item_list[:must_count]
    should = item_list[must_count : must_count + should_count]
    nice = item_list[must_count + should_count :]

    title = str(topic).strip() if topic else "Memory Ladder"

    return {
        "title": title,
        "counts": {
            "must": len(must),
            "should": len(should),
            "nice": len(nice),
        },
        "must": must,
        "should": should,
        "nice": nice,
    }, None
