from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

HEADING_RE = re.compile(r"^(#{1,6})\s*(.*)$")


def structure_hygiene(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    text = (text or "").strip()
    if not text:
        return None, "Provide text to analyze."

    lines = text.splitlines()
    headings: List[Dict[str, Any]] = []
    issues: List[str] = []
    warnings: List[str] = []

    for index, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line.strip())
        if match:
            level = len(match.group(1))
            title = (match.group(2) or "").strip()
            headings.append({"level": level, "text": title, "line": index})
            if not title:
                issues.append(f"Empty heading on line {index}.")

    h1_count = sum(1 for item in headings if item["level"] == 1)
    if h1_count > 1:
        issues.append("Multiple H1 headings found.")

    for prev, current in zip(headings, headings[1:]):
        if current["level"] > prev["level"] + 1:
            warnings.append(
                f"Heading jump from H{prev['level']} to H{current['level']} on line {current['line']}."
            )

    for idx, heading in enumerate(headings):
        start_line = heading["line"]
        end_line = headings[idx + 1]["line"] if idx + 1 < len(headings) else len(lines) + 1
        body_lines = [
            line.strip()
            for line in lines[start_line:end_line - 1]
            if line.strip()
        ]
        if not body_lines:
            warnings.append(f"Heading '{heading['text'] or 'Untitled'}' has no content.")

    return {
        "headings": headings,
        "issues": issues,
        "warnings": warnings,
    }, None
