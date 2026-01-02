from __future__ import annotations

from typing import Any, Dict, Tuple


def map_whitespace(text: str | None) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned = text if text is not None else ""
    if not cleaned.strip():
        return None, "Upload a file or paste text."

    output = []
    counts = {
        "spaces": 0,
        "tabs": 0,
        "lf": 0,
        "crlf": 0,
        "cr": 0,
    }
    double_space_runs = 0
    max_space_run = 0
    space_run = 0

    idx = 0
    while idx < len(cleaned):
        char = cleaned[idx]
        if char == " ":
            counts["spaces"] += 1
            space_run += 1
            output.append("[SPACE]")
            idx += 1
            continue

        if space_run > 1:
            double_space_runs += 1
            if space_run > max_space_run:
                max_space_run = space_run
        space_run = 0

        if char == "\t":
            counts["tabs"] += 1
            output.append("[TAB]")
            idx += 1
            continue

        if char == "\r":
            if idx + 1 < len(cleaned) and cleaned[idx + 1] == "\n":
                counts["crlf"] += 1
                output.append("[CRLF]\n")
                idx += 2
            else:
                counts["cr"] += 1
                output.append("[CR]")
                idx += 1
            continue

        if char == "\n":
            counts["lf"] += 1
            output.append("[LF]\n")
            idx += 1
            continue

        output.append(char)
        idx += 1

    if space_run > 1:
        double_space_runs += 1
        if space_run > max_space_run:
            max_space_run = space_run

    return {
        "counts": counts,
        "double_space_runs": double_space_runs,
        "max_space_run": max_space_run,
        "visualized": "".join(output),
    }, None
