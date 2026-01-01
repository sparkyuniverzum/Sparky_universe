from __future__ import annotations

from typing import Any, Dict, Tuple

from modules.sparky_core.core.structured_data import (
    parse_structured_text,
    profile_rows,
)


def build_snapshot(
    raw_text: str | bytes,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    rows, columns, report, detected, error = parse_structured_text(
        raw_text,
        filename=filename,
        content_type=content_type,
    )
    if error:
        return None, error

    profile = profile_rows(rows, columns)
    summary = {
        "detected_format": detected,
        "row_count": profile["row_count"],
        "column_count": profile["column_count"],
        "empty_rows": profile["empty_rows"],
        "missing_cells": profile["missing_cells"],
        "columns": profile["columns"],
        "report": report,
    }
    return summary, None
