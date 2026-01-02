from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

PATTERNS = [
    ("todo", re.compile(r"\bTODO\b", re.IGNORECASE)),
    ("fixme", re.compile(r"\bFIXME\b", re.IGNORECASE)),
    ("tbd", re.compile(r"\bTBD\b", re.IGNORECASE)),
    ("tba", re.compile(r"\bTBA\b", re.IGNORECASE)),
    ("xxx", re.compile(r"\bXXX\b", re.IGNORECASE)),
    ("lorem", re.compile(r"\blorem(?:\s+ipsum)?\b", re.IGNORECASE)),
    ("placeholder", re.compile(r"\bplaceholder\b", re.IGNORECASE)),
    ("question_marks", re.compile(r"\?{3,}")),
]

BRACKETED = re.compile(r"\[[^\]]{0,40}(todo|tbd|insert|placeholder)[^\]]*\]", re.IGNORECASE)
CURLY = re.compile(r"\{\{[^\}]{1,60}\}\}")


def placeholder_sweep(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    text = (text or "").strip()
    if not text:
        return None, "Provide text to analyze."

    findings: List[Dict[str, Any]] = []
    lines = text.splitlines()
    for line_index, line in enumerate(lines, start=1):
        for label, regex in PATTERNS:
            for match in regex.finditer(line):
                findings.append(
                    {
                        "type": label,
                        "match": match.group(0),
                        "line": line_index,
                        "snippet": line.strip()[:160],
                    }
                )
        for match in BRACKETED.finditer(line):
            findings.append(
                {
                    "type": "bracketed",
                    "match": match.group(0),
                    "line": line_index,
                    "snippet": line.strip()[:160],
                }
            )
        for match in CURLY.finditer(line):
            findings.append(
                {
                    "type": "template_token",
                    "match": match.group(0),
                    "line": line_index,
                    "snippet": line.strip()[:160],
                }
            )

    return {"findings": findings, "finding_count": len(findings)}, None
