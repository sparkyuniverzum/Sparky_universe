from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(value: str) -> List[str]:
    return TOKEN_RE.findall(value)


def _parse_required(raw: str | None) -> List[str]:
    if not raw:
        return []
    parts = re.split(r"[,\n]+", raw)
    return [part.strip() for part in parts if part.strip()]


def validate_campaign_name(
    name: str | None,
    *,
    pattern: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    required_tokens: str | None = None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if not name or not name.strip():
        return None, "Provide a campaign name."

    original = name
    name = name.strip()

    if min_length is not None and max_length is not None and min_length > max_length:
        return None, "Min length cannot be greater than max length."

    regex_match = None
    if pattern:
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            return None, f"Invalid regex: {exc}"
        regex_match = bool(regex.fullmatch(name))

    tokens = _tokenize(name)
    normalized_tokens = {token.lower() for token in tokens}
    required = _parse_required(required_tokens)
    missing = [token for token in required if token.lower() not in normalized_tokens]

    issues: List[str] = []
    warnings: List[str] = []

    if original != name:
        warnings.append("Trimmed leading/trailing whitespace.")

    length = len(name)
    if min_length is not None and length < min_length:
        issues.append(f"Name is shorter than {min_length} characters.")
    if max_length is not None and length > max_length:
        issues.append(f"Name is longer than {max_length} characters.")
    if pattern and regex_match is False:
        issues.append("Name does not match the regex pattern.")
    if missing:
        issues.append(f"Missing required tokens: {', '.join(missing)}.")

    return {
        "input": name,
        "length": length,
        "tokens": tokens,
        "required_tokens": required,
        "missing_tokens": missing,
        "regex": {
            "pattern": pattern,
            "matched": regex_match,
        },
        "limits": {
            "min": min_length,
            "max": max_length,
        },
        "warnings": warnings,
        "issues": issues,
        "valid": len(issues) == 0,
    }, None
