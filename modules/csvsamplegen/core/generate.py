from __future__ import annotations

import csv
import io
import random
from typing import Any, Dict, List, Tuple

from modules.sparky_core.core.rng import make_rng, parse_seed

MAX_ROWS = 500

SAMPLE_VALUES = {
    "name": ["Alex", "Marek", "Nora", "Eva", "Julia"],
    "email": ["alex@example.com", "team@example.com", "info@example.com"],
    "city": ["Prague", "Brno", "Ostrava", "Plzen"],
    "country": ["CZ", "SK", "DE", "PL"],
    "status": ["active", "inactive", "pending"],
}


def _parse_int(value: Any, *, label: str, default: int | None = None) -> Tuple[int | None, str | None]:
    if value is None or str(value).strip() == "":
        if default is None:
            return None, f"{label} is required."
        return default, None
    raw = str(value).strip()
    try:
        number = int(raw)
    except ValueError:
        return None, f"{label} must be a whole number."
    return number, None


def _parse_columns(raw: Any) -> Tuple[List[str] | None, str | None]:
    if raw is None:
        return None, "Columns are required."
    text = str(raw).strip()
    if not text:
        return None, "Columns are required."
    columns = [col.strip() for col in text.split(",") if col.strip()]
    if not columns:
        return None, "Columns are required."
    return columns, None


def _sample_value(column: str, rng: random.Random) -> str:
    key = column.lower()
    for name, values in SAMPLE_VALUES.items():
        if name in key:
            return rng.choice(values)
    if "id" in key:
        return str(rng.randint(1000, 9999))
    if "date" in key:
        return f"2024-0{rng.randint(1,9)}-{rng.randint(10,28)}"
    return f"{key}_{rng.randint(1, 99)}"


def generate_csv_sample(
    columns_raw: Any,
    rows: Any,
    *,
    seed: Any = None,
) -> Tuple[Dict[str, str] | None, str | None]:
    columns, error = _parse_columns(columns_raw)
    if error or columns is None:
        return None, error

    rows_int, error = _parse_int(rows, label="Rows", default=10)
    if error or rows_int is None:
        return None, error

    if rows_int <= 0 or rows_int > MAX_ROWS:
        return None, f"Rows must be between 1 and {MAX_ROWS}."

    seed_int, error = parse_seed(seed)
    if error:
        return None, error
    rng = make_rng(seed_int)
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(columns)

    for _ in range(rows_int):
        row = [_sample_value(col, rng) for col in columns]
        writer.writerow(row)

    return {
        "columns": ",".join(columns),
        "rows": str(rows_int),
        "seed": seed_int,
        "csv": output.getvalue(),
    }, None
