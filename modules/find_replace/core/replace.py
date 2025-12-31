from __future__ import annotations

import re
from typing import Dict, List, Tuple


MAX_SAMPLES = 5


def replace_text(
    text: str | None,
    find: str | None,
    replace_with: str | None,
    *,
    use_regex: bool = False,
    ignore_case: bool = False,
    max_replacements: int = 0,
) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None:
        return None, "Text is required."
    if find is None or not str(find).strip():
        return None, "Find pattern is required."

    pattern = str(find)
    replacement = "" if replace_with is None else str(replace_with)

    flags = re.MULTILINE
    if ignore_case:
        flags |= re.IGNORECASE

    if not use_regex:
        pattern = re.escape(pattern)

    try:
        regex = re.compile(pattern, flags)
    except re.error as exc:
        return None, f"Regex error: {exc}"

    sample_matches: List[str] = []
    for match in regex.finditer(text):
        if len(sample_matches) >= MAX_SAMPLES:
            break
        sample_matches.append(match.group(0))

    replaced_text, count = regex.subn(replacement, text, count=max_replacements)

    return {
        "matches": count,
        "samples": sample_matches,
        "result": replaced_text,
    }, None
