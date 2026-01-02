from __future__ import annotations

from typing import Any, Dict, Tuple


def dedupe_lines(
    text: str | None,
    *,
    case_sensitive: bool = True,
    trim_whitespace: bool = False,
) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned = text if text is not None else ""
    if not cleaned.strip():
        return None, "Upload a file or paste text."

    lines = cleaned.splitlines()
    seen: set[str] = set()
    kept: list[str] = []
    removed = 0

    for line in lines:
        key = line
        if trim_whitespace:
            key = key.strip()
        if not case_sensitive:
            key = key.lower()
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        kept.append(line)

    output = "\n".join(kept)

    return {
        "total_lines": len(lines),
        "unique_lines": len(kept),
        "removed_lines": removed,
        "case_sensitive": case_sensitive,
        "trim_whitespace": trim_whitespace,
        "output": output,
    }, None
