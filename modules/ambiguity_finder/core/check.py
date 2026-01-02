from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

PHRASES = {
    "asap": "Specify a deadline or exact time.",
    "soon": "Replace with an exact time window.",
    "later": "Clarify when it happens.",
    "sometime": "Provide a concrete time.",
    "around": "Use a precise range or number.",
    "approximately": "Give a tighter range.",
    "various": "List the specific items.",
    "several": "Say how many.",
    "some": "Specify the exact items.",
    "many": "Give a count or percentage.",
    "few": "Provide a numeric range.",
    "etc": "List all items or remove this.",
    "and so on": "List the remaining items.",
    "as needed": "Define the trigger or threshold.",
    "as appropriate": "Describe the criteria.",
    "appropriate": "State the specific requirement.",
    "reasonable": "Define what makes it reasonable.",
    "fast": "Define a target time.",
    "quick": "Define a target time.",
    "high quality": "Describe the measurable quality bar.",
    "best effort": "Define the success criteria.",
}


def ambiguity_finder(
    text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    text = (text or "").strip()
    if not text:
        return None, "Provide text to analyze."

    findings: List[Dict[str, Any]] = []
    lower_text = text.lower()

    for phrase, suggestion in PHRASES.items():
        pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
        matches = pattern.findall(lower_text)
        if matches:
            findings.append(
                {
                    "phrase": phrase,
                    "count": len(matches),
                    "suggestion": suggestion,
                }
            )

    return {"ambiguous": findings, "finding_count": len(findings)}, None
