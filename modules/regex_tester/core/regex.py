from __future__ import annotations

import re
from typing import Dict, List, Tuple


MAX_MATCHES = 200
MAX_SAMPLES = 10


def test_regex(
    text: str | None,
    pattern: str | None,
    *,
    ignore_case: bool = False,
    multiline: bool = False,
    dotall: bool = False,
) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None:
        return None, "Text is required."
    if pattern is None or not str(pattern).strip():
        return None, "Pattern is required."

    flags = 0
    if ignore_case:
        flags |= re.IGNORECASE
    if multiline:
        flags |= re.MULTILINE
    if dotall:
        flags |= re.DOTALL

    try:
        regex = re.compile(str(pattern), flags)
    except re.error as exc:
        return None, f"Regex error: {exc}"

    matches: List[Dict[str, object]] = []
    total = 0
    truncated = False

    for match in regex.finditer(text):
        if total >= MAX_MATCHES:
            truncated = True
            break
        total += 1
        if len(matches) < MAX_SAMPLES:
            matches.append(
                {
                    "match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "groups": list(match.groups()),
                }
            )

    flags_list = []
    if ignore_case:
        flags_list.append("ignore_case")
    if multiline:
        flags_list.append("multiline")
    if dotall:
        flags_list.append("dotall")

    return {
        "matches": total,
        "samples": matches,
        "flags": flags_list,
        "truncated": truncated,
    }, None
