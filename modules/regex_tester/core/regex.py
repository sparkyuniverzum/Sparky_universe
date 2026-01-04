from __future__ import annotations

import re
from typing import Dict, List, Tuple


MAX_MATCHES = 200
MAX_SAMPLES = 10
MAX_TEXT_CHARS = 50000
MAX_PATTERN_CHARS = 500
MAX_COMPLEXITY_SCORE = 2000
_NESTED_QUANTIFIER = re.compile(
    r"\((?:[^()\\]|\\.)*([*+]|{\d+,?\d*})\)(?:[*+]|{\d+,?\d*})"
)


def _pattern_too_complex(pattern: str) -> bool:
    if _NESTED_QUANTIFIER.search(pattern):
        return True
    # Rough score: length plus weighted metacharacters to avoid pathological inputs.
    score = len(pattern) + pattern.count("(") * 10 + pattern.count("[") * 5
    score += pattern.count("*") * 15 + pattern.count("+") * 15 + pattern.count("{") * 20
    return score > MAX_COMPLEXITY_SCORE


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
    text_value = str(text)
    pattern_value = str(pattern)
    if len(text_value) > MAX_TEXT_CHARS:
        return None, f"Text is too long (max {MAX_TEXT_CHARS} characters)."
    if len(pattern_value) > MAX_PATTERN_CHARS:
        return None, f"Pattern is too long (max {MAX_PATTERN_CHARS} characters)."
    if _pattern_too_complex(pattern_value):
        return None, "Pattern is too complex to run safely."

    flags = 0
    if ignore_case:
        flags |= re.IGNORECASE
    if multiline:
        flags |= re.MULTILINE
    if dotall:
        flags |= re.DOTALL

    try:
        regex = re.compile(pattern_value, flags)
    except re.error as exc:
        return None, f"Regex error: {exc}"

    matches: List[Dict[str, object]] = []
    total = 0
    truncated = False

    for match in regex.finditer(text_value):
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
