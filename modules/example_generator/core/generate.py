from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _split_lines(value: str | None) -> List[str]:
    if not value:
        return []
    cleaned = value.replace("\r", "").replace(",", "\n")
    return [line.strip() for line in cleaned.split("\n") if line.strip()]


def build_examples(
    concept: str | None,
    domain: str | None,
    items: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if concept is None or not str(concept).strip():
        return None, "Concept is required."

    concept_value = str(concept).strip()
    domain_value = str(domain).strip() if domain else ""
    item_list = _split_lines(items)

    prefix = f"{concept_value}"
    if domain_value:
        prefix = f"{concept_value} in {domain_value}"

    examples: List[str] = []
    if item_list:
        for item in item_list[:3]:
            examples.append(f"Example: {prefix} for {item}.")
    else:
        examples = [
            f"Example 1: {prefix} applied to a real scenario.",
            f"Example 2: {prefix} in a small, concrete case.",
            f"Example 3: {prefix} with a clear outcome.",
        ]

    return {
        "count": len(examples),
        "examples": examples,
    }, None
