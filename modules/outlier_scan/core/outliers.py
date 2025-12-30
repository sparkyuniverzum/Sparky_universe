from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple


MAX_ROWS = 5000
MAX_COLS = 200
MIN_VALUES = 4
NULL_TOKENS = {"", "null", "none", "na", "n/a", "nan"}
NUMERIC_RATIO = Decimal("0.8")


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


def _normalize_number(raw: str) -> str:
    compact = raw.strip().replace(" ", "")
    if "," in compact and "." in compact:
        last_comma = compact.rfind(",")
        last_dot = compact.rfind(".")
        if last_comma > last_dot:
            compact = compact.replace(".", "")
            compact = compact.replace(",", ".")
        else:
            compact = compact.replace(",", "")
    elif "," in compact:
        compact = compact.replace(",", ".")
    return compact


def _parse_decimal(value: str) -> Decimal | None:
    normalized = _normalize_number(value)
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError):
        return None


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


def _median(values: List[Decimal]) -> Decimal:
    count = len(values)
    mid = count // 2
    if count % 2 == 1:
        return values[mid]
    return (values[mid - 1] + values[mid]) / Decimal(2)


def _quartiles(values: List[Decimal]) -> Tuple[Decimal, Decimal]:
    count = len(values)
    mid = count // 2
    lower = values[:mid]
    upper = values[mid:] if count % 2 == 0 else values[mid + 1 :]
    return _median(lower), _median(upper)


def scan_outliers(
    raw_text: str,
    *,
    has_header: bool = True,
) -> Tuple[Dict[str, object] | None, str | None]:
    header, rows, truncated, error = _read_csv(raw_text, has_header=has_header)
    if error or header is None or rows is None:
        return None, error

    col_count = len(header)
    numeric_values: List[List[Decimal]] = [[] for _ in range(col_count)]
    non_empty_counts = [0 for _ in range(col_count)]
    numeric_counts = [0 for _ in range(col_count)]

    for row in rows:
        for idx in range(col_count):
            cell = row[idx] if idx < len(row) else ""
            if _is_null(cell):
                continue
            value = cell.strip()
            if not value:
                continue
            non_empty_counts[idx] += 1
            parsed = _parse_decimal(value)
            if parsed is not None:
                numeric_counts[idx] += 1
                numeric_values[idx].append(parsed)

    results: List[Dict[str, object]] = []
    for idx, name in enumerate(header):
        non_empty = non_empty_counts[idx]
        numeric = numeric_counts[idx]
        if non_empty == 0:
            results.append(
                {"index": idx + 1, "name": name, "status": "empty"}
            )
            continue

        ratio = Decimal(numeric) / Decimal(non_empty) if non_empty else Decimal(0)
        if ratio < NUMERIC_RATIO:
            results.append(
                {
                    "index": idx + 1,
                    "name": name,
                    "status": "non_numeric",
                    "numeric_ratio": float(round(ratio, 3)),
                }
            )
            continue

        values = sorted(numeric_values[idx])
        if len(values) < MIN_VALUES:
            results.append(
                {
                    "index": idx + 1,
                    "name": name,
                    "status": "too_few_values",
                    "numeric_count": len(values),
                }
            )
            continue

        q1, q3 = _quartiles(values)
        iqr = q3 - q1
        low = q1 - (Decimal("1.5") * iqr)
        high = q3 + (Decimal("1.5") * iqr)

        outliers = [value for value in values if value < low or value > high]
        results.append(
            {
                "index": idx + 1,
                "name": name,
                "status": "ok",
                "numeric_count": len(values),
                "q1": str(q1),
                "q3": str(q3),
                "low_cutoff": str(low),
                "high_cutoff": str(high),
                "outlier_count": len(outliers),
                "sample_outliers": [str(value) for value in outliers[:5]],
            }
        )

    return {
        "rows": len(rows),
        "columns": col_count,
        "null_tokens": sorted(token for token in NULL_TOKENS if token),
        "numeric_ratio_threshold": float(NUMERIC_RATIO),
        "truncated": truncated,
        "scan": results,
    }, None
