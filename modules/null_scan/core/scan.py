from __future__ import annotations

import csv
import io
from typing import Dict, List, Tuple


MAX_ROWS = 5000
MAX_COLS = 200
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


def scan_nulls(
    raw_text: str,
    *,
    has_header: bool = True,
) -> Tuple[Dict[str, object] | None, str | None]:
    header, rows, truncated, error = _read_csv(raw_text, has_header=has_header)
    if error or header is None or rows is None:
        return None, error

    col_count = len(header)
    counts = [{"nulls": 0, "non_nulls": 0} for _ in range(col_count)]
    total_nulls = 0

    for row in rows:
        for idx in range(col_count):
            cell = row[idx] if idx < len(row) else ""
            if _is_null(cell):
                counts[idx]["nulls"] += 1
                total_nulls += 1
            else:
                counts[idx]["non_nulls"] += 1

    columns: List[Dict[str, object]] = []
    row_count = len(rows)
    for idx, name in enumerate(header):
        nulls = counts[idx]["nulls"]
        ratio = round(nulls / row_count, 4) if row_count else 0
        columns.append(
            {
                "index": idx + 1,
                "name": name,
                "nulls": nulls,
                "non_nulls": counts[idx]["non_nulls"],
                "null_ratio": ratio,
            }
        )

    overall_ratio = round(total_nulls / (row_count * col_count), 4) if row_count and col_count else 0

    return {
        "rows": row_count,
        "columns": col_count,
        "null_tokens": sorted(token for token in NULL_TOKENS if token),
        "overall_null_ratio": overall_ratio,
        "truncated": truncated,
        "scan": columns,
    }, None
