from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class BriefSection:
    title: str
    lines: List[str]


def _require(value: str | None, name: str) -> Tuple[str | None, str | None]:
    if value is None or str(value).strip() == "":
        return None, f"{name} is required."
    return str(value).strip(), None


def _split_lines(value: str | None) -> List[str]:
    if not value:
        return []
    cleaned = value.replace("\r", "").replace(",", "\n")
    return [line.strip() for line in cleaned.split("\n") if line.strip()]


def build_misconception_brief(
    *,
    topic: str | None,
    audience: str | None,
    misconceptions: str | None,
    corrections: str | None,
    proof_points: str | None,
    examples: str | None,
    constraints: str | None,
    owner: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    topic_value, error = _require(topic, "Topic")
    if error:
        return None, error
    audience_value, error = _require(audience, "Audience")
    if error:
        return None, error

    misconception_list = _split_lines(misconceptions)
    correction_list = _split_lines(corrections)
    if not misconception_list:
        return None, "Misconceptions are required."
    if not correction_list:
        return None, "Corrections are required."

    proof_list = _split_lines(proof_points)
    example_list = _split_lines(examples)
    constraint_list = _split_lines(constraints)
    owner_value = str(owner).strip() if owner else ""

    overview_lines = [f"Topic: {topic_value}", f"Audience: {audience_value}"]
    if owner_value:
        overview_lines.append(f"Owner: {owner_value}")

    pairs: List[str] = []
    max_len = max(len(misconception_list), len(correction_list))
    for idx in range(max_len):
        myth = misconception_list[idx] if idx < len(misconception_list) else "(missing)"
        fact = correction_list[idx] if idx < len(correction_list) else "(correction needed)"
        pairs.append(f"Myth: {myth}")
        pairs.append(f"Fact: {fact}")

    sections: List[BriefSection] = [
        BriefSection(title="Overview", lines=overview_lines),
        BriefSection(title="Myth vs Fact", lines=pairs),
    ]

    if proof_list:
        sections.append(BriefSection(title="Proof points", lines=proof_list))
    if example_list:
        sections.append(BriefSection(title="Examples", lines=example_list))
    if constraint_list:
        sections.append(BriefSection(title="Constraints", lines=constraint_list))

    brief_text_parts: List[str] = [f"Misconception Planet: {topic_value}", ""]
    for section in sections:
        brief_text_parts.append(section.title)
        for line in section.lines:
            brief_text_parts.append(f"- {line}")
        brief_text_parts.append("")

    brief_text = "\n".join(brief_text_parts).strip()

    return {
        "title": f"Misconception Planet: {topic_value}",
        "summary": "Misconceptions mapped and corrected.",
        "sections": [
            {"title": section.title, "lines": section.lines} for section in sections
        ],
        "brief_text": brief_text,
        "sparky": "Misconception brief ready. You can copy and share it.",
    }, None
