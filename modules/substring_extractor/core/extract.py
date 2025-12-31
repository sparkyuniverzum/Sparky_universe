from __future__ import annotations

import re
from typing import Dict, List, Tuple


def _parse_int(value: object, *, label: str) -> Tuple[int | None, str | None]:
    if value is None:
        return None, None
    raw = str(value).strip()
    if not raw:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{label} must be a whole number."


def _extract_slice(text: str, start: int | None, end: int | None) -> str:
    return text[start:end]


def _extract_regex(text: str, pattern: str, group: int) -> Tuple[str, str | None]:
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return "", f"Regex error: {exc}"
    match = regex.search(text)
    if not match:
        return "", None
    try:
        return match.group(group), None
    except IndexError:
        return "", "Regex group index is out of range."


def extract_text(
    text: str | None,
    *,
    mode: str = "slice",
    start: object = None,
    end: object = None,
    pattern: str | None = None,
    group: object = 0,
    per_line: bool = False,
) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None or not text.strip():
        return None, "Text is required."

    mode_key = str(mode or "slice").strip().lower()
    if mode_key not in {"slice", "regex"}:
        return None, "Mode must be slice or regex."

    start_idx, error = _parse_int(start, label="Start")
    if error:
        return None, error
    end_idx, error = _parse_int(end, label="End")
    if error:
        return None, error

    try:
        group_idx = int(str(group).strip())
    except ValueError:
        return None, "Group must be a number."
    if group_idx < 0:
        return None, "Group must be 0 or higher."

    targets = text.splitlines() if per_line else [text]
    results: List[str] = []

    for item in targets:
        if mode_key == "slice":
            results.append(_extract_slice(item, start_idx, end_idx))
        else:
            if not pattern or not str(pattern).strip():
                return None, "Regex pattern is required."
            extracted, error = _extract_regex(item, str(pattern), group_idx)
            if error:
                return None, error
            results.append(extracted)

    return {
        "mode": mode_key,
        "per_line": bool(per_line),
        "items": results,
        "result": "\n".join(results),
    }, None
