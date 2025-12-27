from __future__ import annotations

import csv
import io
from typing import Dict, List, Tuple


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


def parse_column_index(raw: str | None, *, label: str) -> Tuple[int | None, str | None]:
    if not raw or not raw.strip():
        return None, f"{label} key column is required."
    try:
        index = int(raw)
    except ValueError:
        return None, f"{label} key column must be a number."
    if index <= 0:
        return None, f"{label} key column must be 1 or higher."
    return index - 1, None


def _read_rows(raw_text: str) -> Tuple[List[List[str]], csv.Dialect, str | None]:
    if not raw_text.strip():
        return [], _DefaultDialect(), "CSV is empty."

    dialect = _sniff_dialect(raw_text)
    reader = csv.reader(io.StringIO(raw_text), dialect=dialect)
    rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    if not rows:
        return [], dialect, "CSV is empty or invalid."
    return rows, dialect, None


def _build_lookup(
    rows: List[List[str]],
    *,
    key_index: int,
    has_header: bool,
) -> Tuple[Dict[str, List[str]], List[str] | None]:
    start = 1 if has_header else 0
    lookup: Dict[str, List[str]] = {}
    for row in rows[start:]:
        key = row[key_index] if key_index < len(row) else ""
        if key not in lookup:
            lookup[key] = row
    header = rows[0] if has_header and rows else None
    return lookup, header


def merge_csv_text(
    left_text: str,
    right_text: str,
    *,
    left_key: int,
    right_key: int,
    has_headers: bool = False,
) -> Tuple[str, int, int, str | None]:
    left_rows, left_dialect, error = _read_rows(left_text)
    if error:
        return "", 0, 0, f"Left CSV: {error}"

    right_rows, right_dialect, error = _read_rows(right_text)
    if error:
        return "", 0, 0, f"Right CSV: {error}"

    left_lookup, left_header = _build_lookup(
        left_rows, key_index=left_key, has_header=has_headers
    )
    right_lookup, right_header = _build_lookup(
        right_rows, key_index=right_key, has_header=has_headers
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=left_dialect.delimiter, lineterminator="\n")

    if has_headers and left_header:
        merged_header = left_header
        if right_header:
            merged_header = left_header + [
                col for idx, col in enumerate(right_header) if idx != right_key
            ]
        writer.writerow(merged_header)

    merged = 0
    unmatched = 0

    left_iter = left_rows[1:] if has_headers else left_rows
    for row in left_iter:
        key = row[left_key] if left_key < len(row) else ""
        right_row = right_lookup.get(key)
        if not right_row:
            unmatched += 1
            continue

        merged_row = row + [
            cell for idx, cell in enumerate(right_row) if idx != right_key
        ]
        writer.writerow(merged_row)
        merged += 1

    if not output.getvalue():
        return "", 0, 0, "CSV merge produced no output."

    return output.getvalue(), merged, unmatched, None
