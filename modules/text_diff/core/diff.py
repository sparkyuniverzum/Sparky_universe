from __future__ import annotations

import difflib
from typing import Dict, List, Tuple


def diff_texts(
    original: str | None,
    updated: str | None,
    *,
    context: int = 3,
) -> Tuple[Dict[str, object] | None, str | None]:
    if original is None or updated is None:
        return None, "Both texts are required."

    original_lines = original.splitlines()
    updated_lines = updated.splitlines()

    diff_lines = list(
        difflib.unified_diff(
            original_lines,
            updated_lines,
            fromfile="original",
            tofile="updated",
            lineterm="",
            n=context,
        )
    )

    added = 0
    removed = 0
    for line in diff_lines:
        if line.startswith("+++ ") or line.startswith("--- "):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1

    diff_text = "\n".join(diff_lines)

    return {
        "added": added,
        "removed": removed,
        "changed": bool(diff_lines),
        "diff": diff_text,
    }, None
