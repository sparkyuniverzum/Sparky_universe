from __future__ import annotations

import csv
import io
from typing import Dict, Tuple


def _default_dialect() -> csv.Dialect:
    class Default(csv.Dialect):
        delimiter = ","
        quotechar = '"'
        escapechar = None
        doublequote = True
        skipinitialspace = False
        lineterminator = "\n"
        quoting = csv.QUOTE_MINIMAL

    return Default()


def _sniff_dialect(raw_text: str) -> csv.Dialect:
    sample = raw_text[:2048]
    try:
        return csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
    except csv.Error:
        return _default_dialect()


DELIMITER_MAP: Dict[str, str | None] = {
    "auto": None,
    "comma": ",",
    "semicolon": ";",
    "tab": "\t",
    "pipe": "|",
}


def parse_output_delimiter(value: str | None) -> Tuple[str | None, str | None]:
    if not value:
        return None, None
    key = value.strip().lower()
    if key not in DELIMITER_MAP:
        return None, "Unknown delimiter option."
    return DELIMITER_MAP[key], None


def clean_csv_text(
    raw_text: str,
    *,
    trim_cells: bool = True,
    remove_empty_rows: bool = True,
    output_delimiter: str | None = None,
) -> Tuple[str, int, int, str | None]:
    if not raw_text.strip():
        return "", 0, 0, "CSV is empty."

    dialect = _sniff_dialect(raw_text)
    reader = csv.reader(io.StringIO(raw_text), dialect=dialect)
    output = io.StringIO()
    delimiter = output_delimiter or dialect.delimiter
    writer = csv.writer(
        output,
        delimiter=delimiter,
        quotechar=dialect.quotechar,
        escapechar=dialect.escapechar,
        doublequote=dialect.doublequote,
        quoting=dialect.quoting,
        lineterminator="\n",
    )

    kept = 0
    removed = 0

    for row in reader:
        if not row:
            if remove_empty_rows:
                removed += 1
                continue
            writer.writerow([])
            kept += 1
            continue

        cleaned = [cell.strip() if trim_cells else cell for cell in row]
        if remove_empty_rows and not any(cell.strip() for cell in cleaned):
            removed += 1
            continue

        writer.writerow(cleaned)
        kept += 1

    if not output.getvalue():
        return "", 0, 0, "CSV is empty or invalid."

    return output.getvalue(), kept, removed, None
