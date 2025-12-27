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
        return None, "Select at least one column."

    indexes: List[int] = []
    seen: set[int] = set()
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
        zero_based = index - 1
        if zero_based in seen:
            continue
        seen.add(zero_based)
        indexes.append(zero_based)

    if not indexes:
        return None, "Select at least one column."

    return indexes, None


def _pick_columns(row: Iterable[str], indexes: List[int]) -> List[str]:
    row_list = list(row)
    return [row_list[index] if index < len(row_list) else "" for index in indexes]


def extract_csv_text(
    raw_text: str,
    *,
    columns: List[int],
    has_header: bool = False,
) -> Tuple[str, int, str | None]:
    if not raw_text.strip():
        return "", 0, "CSV is empty."

    dialect = _sniff_dialect(raw_text)
    reader = csv.reader(io.StringIO(raw_text), dialect=dialect)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=dialect.delimiter, lineterminator="\n")

    extracted = 0
    header_written = False

    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue

        if has_header and not header_written:
            writer.writerow(_pick_columns(row, columns))
            header_written = True
            continue

        writer.writerow(_pick_columns(row, columns))
        extracted += 1

    if not output.getvalue():
        return "", 0, "CSV is empty or invalid."

    return output.getvalue(), extracted, None
