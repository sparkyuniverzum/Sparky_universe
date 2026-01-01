from __future__ import annotations

from typing import Any, Dict, List, Tuple

from modules.sparky_core.core.structured_data import (
    parse_structured_text,
    profile_rows,
    row_signatures,
)


def _value_type(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        int(raw)
        return "int"
    except ValueError:
        pass
    try:
        float(raw)
        return "float"
    except ValueError:
        return "text"


def _column_type_summary(rows: List[Dict[str, Any]], columns: List[str]) -> Dict[str, str]:
    summary: Dict[str, str] = {}
    for column in columns:
        types = set()
        for row in rows:
            detected = _value_type(row.get(column))
            if detected:
                types.add(detected)
            if len(types) > 1:
                break
        if not types:
            summary[column] = "empty"
        elif len(types) == 1:
            summary[column] = next(iter(types))
        else:
            summary[column] = "mixed"
    return summary


def build_readiness(
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
    signatures = row_signatures(rows, columns)
    total = len(signatures)
    unique = len(set(signatures))
    duplicates = total - unique
    duplicate_ratio = duplicates / total if total else 0
    missing_cells = profile["missing_cells"]
    missing_ratio = (
        missing_cells / (profile["row_count"] * profile["column_count"])
        if profile["row_count"] and profile["column_count"]
        else 0
    )
    type_summary = _column_type_summary(rows, columns)
    mixed_columns = [col for col, typ in type_summary.items() if typ == "mixed"]

    verdict = "ok"
    reasons: List[str] = []
    if missing_ratio > 0.25 or duplicate_ratio > 0.2:
        verdict = "fail"
    elif missing_ratio > 0.1 or duplicate_ratio > 0.05 or mixed_columns:
        verdict = "warn"

    if missing_ratio > 0:
        reasons.append(f"missing ratio {missing_ratio:.1%}")
    if duplicate_ratio > 0:
        reasons.append(f"duplicate ratio {duplicate_ratio:.1%}")
    if mixed_columns:
        reasons.append(f"mixed types in {len(mixed_columns)} columns")

    payload = {
        "detected_format": detected,
        "verdict": verdict,
        "reasons": reasons,
        "row_count": profile["row_count"],
        "column_count": profile["column_count"],
        "missing_ratio": missing_ratio,
        "duplicate_ratio": duplicate_ratio,
        "mixed_columns": mixed_columns[:10],
        "type_summary": type_summary,
        "report": report,
    }
    return payload, None
