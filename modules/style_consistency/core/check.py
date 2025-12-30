from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

TITLE_WORDS_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")

NUMBER_WORDS = {
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
}

OXFORD_RE = re.compile(r"\\b\\w+,\\s+\\w+,\\s+and\\s+\\w+\\b", re.IGNORECASE)
NO_OXFORD_RE = re.compile(r"\\b\\w+,\\s+\\w+\\s+and\\s+\\w+\\b", re.IGNORECASE)


def _detect_headline_case(headline: str) -> str:
    words = TITLE_WORDS_RE.findall(headline)
    if not words:
        return "unknown"
    title_count = sum(1 for word in words if word[0].isupper())
    ratio = title_count / len(words)
    if ratio >= 0.7:
        return "title"
    if headline[:1].isupper():
        return "sentence"
    return "unknown"


def style_check(
    *,
    headline: str | None,
    body: str | None,
    preferred_case: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    headline = (headline or "").strip()
    body = (body or "").strip()
    preferred_case = (preferred_case or "auto").strip().lower()
    if preferred_case not in {"auto", "title", "sentence"}:
        preferred_case = "auto"

    if not headline and not body:
        return None, "Provide headline or body text."

    issues: List[str] = []
    warnings: List[str] = []

    has_single_quotes = "'" in body or "'" in headline
    has_double_quotes = '"' in body or '"' in headline
    if has_single_quotes and has_double_quotes:
        warnings.append("Mixed single and double quotes found.")

    oxford_hits = len(OXFORD_RE.findall(body))
    no_oxford_hits = len(NO_OXFORD_RE.findall(body))
    if oxford_hits and no_oxford_hits:
        warnings.append("Oxford comma usage is inconsistent.")

    lower_body = body.lower()
    digit_hits = re.findall(r"\\b\\d+\\b", lower_body)
    word_hits = [word for word in NUMBER_WORDS if word in lower_body]
    if digit_hits and word_hits:
        warnings.append("Mixing digits and spelled-out numbers (1-9).")

    detected_case = _detect_headline_case(headline) if headline else "unknown"
    if preferred_case != "auto" and detected_case != "unknown":
        if detected_case != preferred_case:
            issues.append(f"Headline case is {detected_case}, expected {preferred_case}.")

    return {
        "preferred_case": preferred_case,
        "detected_case": detected_case,
        "quotes": {
            "single": has_single_quotes,
            "double": has_double_quotes,
        },
        "oxford_comma": {
            "with": oxford_hits,
            "without": no_oxford_hits,
        },
        "numbers": {
            "digits": len(digit_hits),
            "words": len(word_hits),
        },
        "issues": issues,
        "warnings": warnings,
    }, None
