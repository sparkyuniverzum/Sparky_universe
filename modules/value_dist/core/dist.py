from __future__ import annotations

import csv
import io
from typing import Dict, List, Tuple


MAX_ROWS = 5000
MAX_COLS = 200
MAX_UNIQUE = 2000
NULL_TOKENS = {"", "null", "none", "na", "n/a", "nan"}


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


def _resolve_column(header: List[str], column_raw: str) -> Tuple[int | None, str | None]:
    if not column_raw or not column_raw.strip():
        return None, "Column is required."
    token = column_raw.strip()
    if token.isdigit():
        idx = int(token) - 1
        if idx < 0 or idx >= len(header):
            return None, "Column index is out of range."
        return idx, None
    lowered = token.lower()
    for idx, name in enumerate(header):
        if name.lower() == lowered:
            return idx, None
    return None, "Column name not found in header."


def value_distribution(
    raw_text: str,
    column: str,
    *,
    has_header: bool = True,
    top_n: int = 10,
) -> Tuple[Dict[str, object] | None, str | None]:
    header, rows, truncated, error = _read_csv(raw_text, has_header=has_header)
    if error or header is None or rows is None:
        return None, error

    column_idx, error = _resolve_column(header, column)
    if error or column_idx is None:
        return None, error

    counts: Dict[str, int] = {}
    other_count = 0
    nulls = 0

    for row in rows:
        value = row[column_idx] if column_idx < len(row) else ""
        if _is_null(value):
            nulls += 1
            continue
        clean = value.strip()
        if not clean:
            nulls += 1
            continue
        if clean in counts:
            counts[clean] += 1
        else:
            if len(counts) < MAX_UNIQUE:
                counts[clean] = 1
            else:
                other_count += 1

    items = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    top_items = [
        {"value": value, "count": count} for value, count in items[:top_n]
    ]

    return {
        "rows": len(rows),
        "column": header[column_idx],
        "column_index": column_idx + 1,
        "unique_values": len(counts),
        "unique_overflow": other_count > 0,
        "nulls": nulls,
        "top_values": top_items,
        "other_count": other_count,
        "truncated": truncated,
    }, None
