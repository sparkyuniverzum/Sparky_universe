from __future__ import annotations

import csv
import io
from typing import Iterable, List, Tuple


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


def parse_column_indexes(raw: str | None) -> Tuple[List[int] | None, str | None]:
    if not raw or not raw.strip():
        return None, None

    indexes: List[int] = []
    for chunk in raw.split(","):
        token = chunk.strip()
        if not token:
            continue
        try:
            index = int(token)
        except ValueError:
            return None, "Columns must be numbers separated by commas."
        if index <= 0:
            return None, "Columns must be 1 or higher."
        indexes.append(index - 1)

    if not indexes:
        return None, None

    return indexes, None


def _row_key(row: Iterable[str], indexes: List[int] | None) -> Tuple[str, ...]:
    row_list = list(row)
    if not indexes:
        return tuple(row_list)
    key: List[str] = []
    for index in indexes:
        key.append(row_list[index] if index < len(row_list) else "")
    return tuple(key)


def dedupe_csv_text(
    raw_text: str,
    *,
    columns: List[int] | None = None,
    has_header: bool = False,
) -> Tuple[str, int, int, str | None]:
    if not raw_text.strip():
        return "", 0, 0, "CSV is empty."

    dialect = _sniff_dialect(raw_text)
    reader = csv.reader(io.StringIO(raw_text), dialect=dialect)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=dialect.delimiter, lineterminator="\n")

    seen: set[Tuple[str, ...]] = set()
    removed = 0
    total = 0
    header_written = False

    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue

        if has_header and not header_written:
            writer.writerow(row)
            header_written = True
            continue

        key = _row_key(row, columns)
        if key in seen:
            removed += 1
            continue

        seen.add(key)
        writer.writerow(row)
        total += 1

    if not output.getvalue():
        return "", 0, 0, "CSV is empty or invalid."

    return output.getvalue(), removed, total, None
