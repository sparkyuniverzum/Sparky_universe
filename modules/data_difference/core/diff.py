from __future__ import annotations

from typing import Any, Dict, List, Tuple

from modules.sparky_core.core.structured_data import parse_structured_text, row_signatures


def _normalize_columns(rows_a: List[Dict[str, Any]], rows_b: List[Dict[str, Any]]) -> List[str]:
    columns: List[str] = []
    seen = set()
    for row in rows_a + rows_b:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def _parse_keys(raw: str | None, columns: List[str]) -> Tuple[List[str] | None, str | None]:
    if not raw or not raw.strip():
        return None, None
    keys = [item.strip() for item in raw.split(",") if item.strip()]
    if not keys:
        return None, None
    missing = [key for key in keys if key not in columns]
    if missing:
        return None, f"Unknown key columns: {', '.join(missing)}"
    return keys, None


def _row_key(row: Dict[str, Any], keys: List[str]) -> Tuple[str, ...]:
    return tuple(str(row.get(key, "")).strip() for key in keys)


def diff_datasets(
    raw_a: str | bytes,
    raw_b: str | bytes,
    *,
    filename_a: str | None = None,
    filename_b: str | None = None,
    content_type_a: str | None = None,
    content_type_b: str | None = None,
    key_columns: str | None = None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    rows_a, _, report_a, fmt_a, error_a = parse_structured_text(
        raw_a, filename=filename_a, content_type=content_type_a
    )
    if error_a:
        return None, error_a
    rows_b, _, report_b, fmt_b, error_b = parse_structured_text(
        raw_b, filename=filename_b, content_type=content_type_b
    )
    if error_b:
        return None, error_b

    columns = _normalize_columns(rows_a, rows_b)
    keys, error = _parse_keys(key_columns, columns)
    if error:
        return None, error

    added_samples: List[Any] = []
    removed_samples: List[Any] = []
    changed_samples: List[Any] = []

    if keys:
        map_a = { _row_key(row, keys): row for row in rows_a }
        map_b = { _row_key(row, keys): row for row in rows_b }
        keys_a = set(map_a.keys())
        keys_b = set(map_b.keys())
        added_keys = keys_b - keys_a
        removed_keys = keys_a - keys_b
        shared_keys = keys_a & keys_b

        changed = 0
        for key in list(shared_keys)[:50]:
            row_a = map_a[key]
            row_b = map_b[key]
            if row_a != row_b:
                changed += 1
                if len(changed_samples) < 5:
                    changed_samples.append({"key": key, "before": row_a, "after": row_b})

        for key in list(added_keys)[:5]:
            added_samples.append({"key": key, "row": map_b[key]})
        for key in list(removed_keys)[:5]:
            removed_samples.append({"key": key, "row": map_a[key]})

        summary = {
            "added": len(added_keys),
            "removed": len(removed_keys),
            "changed": changed,
        }
    else:
        signatures_a = set(row_signatures(rows_a, columns))
        signatures_b = set(row_signatures(rows_b, columns))
        added = signatures_b - signatures_a
        removed = signatures_a - signatures_b
        summary = {
            "added": len(added),
            "removed": len(removed),
            "changed": 0,
        }
        for item in list(added)[:5]:
            added_samples.append(item)
        for item in list(removed)[:5]:
            removed_samples.append(item)

    payload = {
        "format_a": fmt_a,
        "format_b": fmt_b,
        "row_count_a": len(rows_a),
        "row_count_b": len(rows_b),
        "columns": columns,
        "summary": summary,
        "added_samples": added_samples,
        "removed_samples": removed_samples,
        "changed_samples": changed_samples,
        "report_a": report_a,
        "report_b": report_b,
        "key_columns": keys or [],
    }
    return payload, None
