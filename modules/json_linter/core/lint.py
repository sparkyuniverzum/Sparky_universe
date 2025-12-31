from __future__ import annotations

import json
from typing import Any, Tuple


MAX_DEPTH = 15
MAX_KEYS = 5000


def _summarize(node: Any, *, depth: int = 0) -> Tuple[int, int]:
    if depth > MAX_DEPTH:
        return 0, 0

    if isinstance(node, dict):
        key_count = len(node)
        total_keys = key_count
        max_depth = depth
        for value in node.values():
            child_keys, child_depth = _summarize(value, depth=depth + 1)
            total_keys += child_keys
            max_depth = max(max_depth, child_depth)
            if total_keys >= MAX_KEYS:
                break
        return total_keys, max_depth

    if isinstance(node, list):
        total_keys = 0
        max_depth = depth
        for item in node:
            child_keys, child_depth = _summarize(item, depth=depth + 1)
            total_keys += child_keys
            max_depth = max(max_depth, child_depth)
            if total_keys >= MAX_KEYS:
                break
        return total_keys, max_depth

    return 0, depth


def lint_json(
    raw_text: str | None,
    *,
    indent: int = 2,
    sort_keys: bool = False,
) -> Tuple[dict[str, object] | None, str | None]:
    if raw_text is None or not raw_text.strip():
        return None, "JSON input is required."

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return None, f"JSON error at line {exc.lineno}, column {exc.colno}: {exc.msg}"
    except RecursionError:
        return None, "JSON is too deeply nested to analyze."

    keys, depth = _summarize(data, depth=0)
    pretty = json.dumps(
        data,
        ensure_ascii=True,
        indent=indent,
        sort_keys=sort_keys,
    )
    minified = json.dumps(data, separators=(",", ":"), ensure_ascii=True)

    return {
        "valid": True,
        "type": type(data).__name__,
        "keys": min(keys, MAX_KEYS),
        "max_depth": depth,
        "pretty": pretty,
        "minified": minified,
    }, None
