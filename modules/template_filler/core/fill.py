from __future__ import annotations

import re
from typing import Dict, Tuple


PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")


def _parse_mapping(raw: str | None) -> Tuple[Dict[str, str] | None, str | None]:
    if raw is None or not raw.strip():
        return None, "Mapping is required."

    mapping: Dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if "=" not in line:
            return None, "Mapping lines must use key=value."
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            return None, "Mapping key is required."
        mapping[key] = value.strip()
    if not mapping:
        return None, "Mapping is required."
    return mapping, None


def fill_template(
    text: str | None,
    mapping_text: str | None,
    *,
    strict: bool = False,
) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None or not text.strip():
        return None, "Template text is required."

    mapping, error = _parse_mapping(mapping_text)
    if error or mapping is None:
        return None, error

    missing = set()
    used = set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in mapping:
            used.add(key)
            return mapping[key]
        missing.add(key)
        return match.group(0)

    result = PLACEHOLDER_RE.sub(replace, text)
    if strict and missing:
        return None, f"Missing values for: {', '.join(sorted(missing))}"

    return {
        "result": result,
        "used_keys": sorted(used),
        "missing_keys": sorted(missing),
    }, None
