from __future__ import annotations

import csv
import io
from typing import Dict, List, Tuple


MAX_ROWS = 5000
MAX_COLS = 200
NULL_TOKENS = {"", "null", "none", "na", "n/a", "nan"}
SAMPLE_KEYS = 5


class _DefaultDialect(csv.Dialect):
    delimiter = ","
    quotechar = '"'
    escapechar = None
    doublequote = True
    skipinitialspace = False
    lineterminator = "\n"
    quoting = csv.QUOTE_MINIMAL


def _sniff_dialect(raw_text: str) -> csv.Dialect:
    sample = raw_text[:2048]
    try:
        return csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
    except csv.Error:
        return _DefaultDialect()


def _is_null(value: str) -> bool:
    return value.strip().lower() in NULL_TOKENS


def _read_csv(
    raw_text: str, *, has_header: bool
) -> Tuple[List[str] | None, List[List[str]] | None, bool, str | None]:
    if not raw_text.strip():
        return None, None, False, "CSV is empty."

    dialect = _sniff_dialect(raw_text)
    reader = csv.reader(io.StringIO(raw_text), dialect=dialect)
    rows: List[List[str]] = []
    header: List[str] | None = None
    truncated = False

    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue
        if header is None and has_header:
            header = [cell.strip() or f"column_{idx + 1}" for idx, cell in enumerate(row)]
            continue
        rows.append(row)
        if len(rows) >= MAX_ROWS:
            truncated = True
            break

    if header is None:
        max_cols = max((len(row) for row in rows), default=0)
        header = [f"column_{idx + 1}" for idx in range(max_cols)]
    else:
        max_cols = max((len(row) for row in rows), default=len(header))
        if max_cols > len(header):
            header.extend(
                f"column_{idx + 1}" for idx in range(len(header), max_cols)
            )

    if len(header) > MAX_COLS:
        return None, None, False, f"Too many columns (limit {MAX_COLS})."

    return header, rows, truncated, None


def _resolve_key(header: List[str], key_raw: str) -> Tuple[int | None, str | None]:
    if not key_raw or not key_raw.strip():
        return None, "Join key is required."
    token = key_raw.strip()
    if token.isdigit():
        idx = int(token) - 1
        if idx < 0 or idx >= len(header):
            return None, "Join key index is out of range."
        return idx, None

    lowered = token.lower()
    for idx, name in enumerate(header):
        if name.lower() == lowered:
            return idx, None
    return None, "Join key not found in header."


def _collect_keys(rows: List[List[str]], key_idx: int) -> Tuple[set[str], int, int, List[str]]:
    keys: set[str] = set()
    missing = 0
    duplicates = 0
    samples: List[str] = []
    for row in rows:
        value = row[key_idx] if key_idx < len(row) else ""
        if _is_null(value):
            missing += 1
            continue
        key = value.strip()
        if not key:
            missing += 1
            continue
        if key in keys:
            duplicates += 1
        else:
            keys.add(key)
            if len(samples) < SAMPLE_KEYS:
                samples.append(key)
    return keys, missing, duplicates, samples


def preview_join(
    left_text: str,
    right_text: str,
    *,
    left_key: str,
    right_key: str,
    left_header: bool = True,
    right_header: bool = True,
) -> Tuple[Dict[str, object] | None, str | None]:
    left_header_list, left_rows, left_truncated, error = _read_csv(
        left_text, has_header=left_header
    )
    if error or left_header_list is None or left_rows is None:
        return None, error

    right_header_list, right_rows, right_truncated, error = _read_csv(
        right_text, has_header=right_header
    )
    if error or right_header_list is None or right_rows is None:
        return None, error

    left_idx, error = _resolve_key(left_header_list, left_key)
    if error or left_idx is None:
        return None, f"Left key error: {error}"
    right_idx, error = _resolve_key(right_header_list, right_key)
    if error or right_idx is None:
        return None, f"Right key error: {error}"

    left_keys, left_missing, left_duplicates, left_sample = _collect_keys(
        left_rows, left_idx
    )
    right_keys, right_missing, right_duplicates, right_sample = _collect_keys(
        right_rows, right_idx
    )

    matches = left_keys & right_keys
    left_only = left_keys - right_keys
    right_only = right_keys - left_keys

    left_count = len(left_keys)
    right_count = len(right_keys)
    match_count = len(matches)

    return {
        "left_rows": len(left_rows),
        "right_rows": len(right_rows),
        "left_key": left_header_list[left_idx],
        "right_key": right_header_list[right_idx],
        "left_unique_keys": left_count,
        "right_unique_keys": right_count,
        "matches": match_count,
        "left_only": len(left_only),
        "right_only": len(right_only),
        "left_missing_keys": left_missing,
        "right_missing_keys": right_missing,
        "left_duplicates": left_duplicates,
        "right_duplicates": right_duplicates,
        "left_match_rate": round(match_count / left_count, 4) if left_count else 0,
        "right_match_rate": round(match_count / right_count, 4) if right_count else 0,
        "sample_matches": sorted(matches)[:SAMPLE_KEYS],
        "sample_left_only": sorted(left_only)[:SAMPLE_KEYS],
        "sample_right_only": sorted(right_only)[:SAMPLE_KEYS],
        "left_sample_keys": left_sample,
        "right_sample_keys": right_sample,
        "left_truncated": left_truncated,
        "right_truncated": right_truncated,
    }, None
