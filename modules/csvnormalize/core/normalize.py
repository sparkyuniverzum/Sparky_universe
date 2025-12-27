from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Tuple

Q4 = Decimal("0.0001")
Q3 = Decimal("0.001")
Q2 = Decimal("0.01")


def _sanitize(value: str) -> str:
    return value.strip().replace(" ", "").replace(",", ".")


def _parse_decimal(value: Any) -> Tuple[Decimal | None, str | None]:
    if value is None:
        return None, "Value is required."
    raw = str(value)
    if not raw.strip():
        return None, "Value is required."

    normalized = _sanitize(raw)
    try:
        return Decimal(normalized), None
    except (InvalidOperation, ValueError):
        return None, "Invalid number format."


def _format_number(value: Any) -> Tuple[Dict[str, str] | None, str | None]:
    decimal, error = _parse_decimal(value)
    if error or decimal is None:
        return None, error

    result = {
        "normalized": _sanitize(str(value)),
        "money_out": format(decimal, "f"),
        "q2": str(decimal.quantize(Q2, rounding=ROUND_HALF_UP)),
        "q3": str(decimal.quantize(Q3, rounding=ROUND_HALF_UP)),
        "q4": str(decimal.quantize(Q4, rounding=ROUND_HALF_UP)),
    }
    return result, None


def _sniff_dialect(raw_text: str) -> csv.Dialect:
    sample = raw_text[:2048]
    try:
        return csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
    except csv.Error:
        class Default(csv.Dialect):
            delimiter = ","
            quotechar = "\""
            escapechar = None
            doublequote = True
            skipinitialspace = False
            lineterminator = "\n"
            quoting = csv.QUOTE_MINIMAL

        return Default()


def normalize_csv_text(raw_text: str, *, column_index: int = 0) -> Tuple[str, int]:
    if not raw_text.strip():
        return "", 0

    dialect = _sniff_dialect(raw_text)
    reader = csv.reader(io.StringIO(raw_text), dialect=dialect)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=dialect.delimiter, lineterminator="\n")

    processed = 0
    header_checked = False

    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue

        if not header_checked:
            header_checked = True
            candidate = row[column_index] if column_index < len(row) else ""
            _, error = _format_number(candidate)
            if error:
                header = row + ["normalized", "money_out", "q2", "q3", "q4", "error"]
                writer.writerow(header)
                continue

        value = row[column_index] if column_index < len(row) else ""
        result, error = _format_number(value)
        if error:
            writer.writerow(row + ["", "", "", "", "", error])
        else:
            writer.writerow(
                row
                + [
                    result["normalized"],
                    result["money_out"],
                    result["q2"],
                    result["q3"],
                    result["q4"],
                    "",
                ]
            )
        processed += 1

    return output.getvalue(), processed
