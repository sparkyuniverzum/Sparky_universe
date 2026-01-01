from __future__ import annotations

from typing import Any, Dict, List, Tuple

from modules.sparky_core.core.structured_data import (
    parse_structured_text,
    rows_to_csv,
    rows_to_json,
    rows_to_xlsx_bytes,
)


def translate_payload(
    raw_text: str | bytes,
    *,
    filename: str | None = None,
    content_type: str | None = None,
    output_format: str = "json",
) -> Tuple[Dict[str, Any] | bytes | None, str | None, str]:
    rows, columns, report, detected, error = parse_structured_text(
        raw_text,
        filename=filename,
        content_type=content_type,
    )
    if error:
        return None, error, "application/json"

    normalized_format = output_format.lower().strip()
    if normalized_format not in {"json", "csv", "xlsx"}:
        return None, "Output format must be json, csv, or xlsx.", "application/json"
    if normalized_format == "xlsx":
        output_bytes = rows_to_xlsx_bytes(rows, columns)
        return (
            output_bytes,
            None,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    output = rows_to_json(rows) if normalized_format == "json" else rows_to_csv(rows, columns)
    preview = output[:4000]

    result = {
        "detected_format": detected,
        "rows": len(rows),
        "columns": columns,
        "output_format": normalized_format,
        "output_preview": preview,
        "report": report,
    }
    return result, None, "application/json"
