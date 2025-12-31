from __future__ import annotations

from typing import Dict, List, Tuple


def process_lines(
    text: str | None,
    *,
    trim_lines: bool = True,
    remove_empty: bool = False,
    dedupe: bool = False,
    sort_mode: str = "none",
    reverse: bool = False,
    case_sensitive: bool = True,
) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None or not text.strip():
        return None, "Text is required."

    sort_key = sort_mode.strip().lower()
    if sort_key not in {"none", "asc", "desc"}:
        return None, "Sort mode must be none, asc, or desc."

    lines = text.splitlines()
    original_count = len(lines)
    processed: List[str] = []
    seen = set()
    removed_dupes = 0

    for line in lines:
        value = line.strip() if trim_lines else line
        if remove_empty and not value:
            continue
        key = value if case_sensitive else value.lower()
        if dedupe:
            if key in seen:
                removed_dupes += 1
                continue
            seen.add(key)
        processed.append(value)

    if sort_key != "none":
        processed.sort(key=lambda item: item if case_sensitive else item.lower())
        if sort_key == "desc":
            processed.reverse()

    if reverse:
        processed = list(reversed(processed))

    return {
        "original_lines": original_count,
        "final_lines": len(processed),
        "removed_lines": original_count - len(processed),
        "removed_duplicates": removed_dupes,
        "lines": processed,
        "result": "\n".join(processed),
    }, None
