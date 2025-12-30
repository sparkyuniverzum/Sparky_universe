from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple


MAX_ROWS = 5000
MAX_COLS = 200
MAX_UNIQUE = 2000
MAX_EXAMPLES = 3
NULL_TOKENS = {"", "null", "none", "na", "n/a", "nan"}
BOOL_TOKENS = {"true", "false", "yes", "no", "y", "n"}
INT_RE = re.compile(r"^[+-]?\d+$")
FLOAT_RE = re.compile(r"^[+-]?(?:\d+\.\d+|\d+|\.\d+)(?:[eE][+-]?\d+)?$")


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


def _is_null(value: str) -> bool:
    return value.strip().lower() in NULL_TOKENS


def _looks_like_date(value: str) -> bool:
    return "-" in value or "T" in value


def _classify(value: str) -> Tuple[str, Decimal | None]:
    lowered = value.strip().lower()
    if lowered in BOOL_TOKENS:
        return "bool", None

    normalized = _normalize_number(value)
    if INT_RE.match(normalized):
        try:
            return "int", Decimal(normalized)
        except (InvalidOperation, ValueError):
            return "string", None
    if FLOAT_RE.match(normalized):
        try:
            return "float", Decimal(normalized)
        except (InvalidOperation, ValueError):
            return "string", None

    if _looks_like_date(value):
        try:
            datetime.fromisoformat(value.strip())
            return "date", None
        except ValueError:
            pass

    return "string", None


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


def profile_schema(
    raw_text: str,
    *,
    has_header: bool = True,
) -> Tuple[Dict[str, object] | None, str | None]:
    header, rows, truncated, error = _read_csv(raw_text, has_header=has_header)
    if error or header is None or rows is None:
        return None, error

    col_count = len(header)
    stats: List[Dict[str, object]] = []
    for _ in range(col_count):
        stats.append(
            {
                "empty": 0,
                "non_empty": 0,
                "types": {"int": 0, "float": 0, "bool": 0, "date": 0, "string": 0},
                "min": None,
                "max": None,
                "min_len": None,
                "max_len": None,
                "unique": set(),
                "unique_overflow": False,
                "examples": [],
            }
        )

    for row in rows:
        for idx in range(col_count):
            cell = row[idx] if idx < len(row) else ""
            if _is_null(cell):
                stats[idx]["empty"] += 1
                continue

            value = cell.strip()
            if not value:
                stats[idx]["empty"] += 1
                continue

            stats[idx]["non_empty"] += 1
            types = stats[idx]["types"]
            kind, numeric = _classify(value)
            types[kind] += 1

            if kind in {"int", "float"} and numeric is not None:
                current_min = stats[idx]["min"]
                current_max = stats[idx]["max"]
                if current_min is None or numeric < current_min:
                    stats[idx]["min"] = numeric
                if current_max is None or numeric > current_max:
                    stats[idx]["max"] = numeric
            elif kind == "string":
                length = len(value)
                min_len = stats[idx]["min_len"]
                max_len = stats[idx]["max_len"]
                if min_len is None or length < min_len:
                    stats[idx]["min_len"] = length
                if max_len is None or length > max_len:
                    stats[idx]["max_len"] = length

            unique = stats[idx]["unique"]
            if not stats[idx]["unique_overflow"]:
                if len(unique) < MAX_UNIQUE:
                    unique.add(value)
                else:
                    stats[idx]["unique_overflow"] = True

            if len(stats[idx]["examples"]) < MAX_EXAMPLES:
                if value not in stats[idx]["examples"]:
                    stats[idx]["examples"].append(value)

    columns: List[Dict[str, object]] = []
    for idx, name in enumerate(header):
        meta = stats[idx]
        non_empty = meta["non_empty"]
        empty = meta["empty"]
        types = meta["types"]
        detected = "empty" if non_empty == 0 else "mixed"
        if non_empty:
            if types["int"] + types["float"] == non_empty:
                detected = "int" if types["float"] == 0 else "float"
            elif types["bool"] == non_empty:
                detected = "bool"
            elif types["date"] == non_empty:
                detected = "date"
            elif types["string"] == non_empty:
                detected = "string"

        top_count = max(types.values()) if non_empty else 0
        confidence = round(top_count / non_empty, 3) if non_empty else 0

        unique_count: object
        if meta["unique_overflow"]:
            unique_count = f">={MAX_UNIQUE}"
        else:
            unique_count = len(meta["unique"])

        columns.append(
            {
                "index": idx + 1,
                "name": name,
                "type": detected,
                "confidence": confidence,
                "non_empty": non_empty,
                "empty": empty,
                "unique": unique_count,
                "min": str(meta["min"]) if meta["min"] is not None else None,
                "max": str(meta["max"]) if meta["max"] is not None else None,
                "min_len": meta["min_len"],
                "max_len": meta["max_len"],
                "examples": meta["examples"],
            }
        )

    return {
        "rows": len(rows),
        "columns": col_count,
        "null_tokens": sorted(token for token in NULL_TOKENS if token),
        "truncated": truncated,
        "profile": columns,
    }, None
