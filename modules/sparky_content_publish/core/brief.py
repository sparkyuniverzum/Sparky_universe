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


def _optional(value: str | None) -> str:
    return str(value).strip() if value else ""


def build_publish_brief(
    *,
    title: str | None,
    objective: str | None,
    audience: str | None,
    message: str | None,
    cta: str | None,
    channel: str | None,
    format_type: str | None,
    publish_date: str | None,
    tone: str | None,
    assets: str | None,
    proof_points: str | None,
    sources: str | None,
    approvals: str | None,
    constraints: str | None,
    owner: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    objective_value, error = _require(objective, "Objective")
    if error:
        return None, error
    audience_value, error = _require(audience, "Audience")
    if error:
        return None, error
    message_value, error = _require(message, "Key message")
    if error:
        return None, error
    cta_value, error = _require(cta, "Primary CTA")
    if error:
        return None, error
    channel_value, error = _require(channel, "Primary channel")
    if error:
        return None, error
    format_value, error = _require(format_type, "Format")
    if error:
        return None, error

    title_value = _optional(title) or "Publish Brief"
    publish_value = _optional(publish_date)
    tone_value = _optional(tone)
    owner_value = _optional(owner)

    asset_list = _split_lines(assets)
    proof_list = _split_lines(proof_points)
    source_list = _split_lines(sources)
    approval_list = _split_lines(approvals)
    constraint_list = _split_lines(constraints)

    overview_lines = [
        f"Objective: {objective_value}",
        f"Channel: {channel_value}",
        f"Format: {format_value}",
    ]
    if publish_value:
        overview_lines.append(f"Publish date: {publish_value}")
    if owner_value:
        overview_lines.append(f"Owner: {owner_value}")

    message_lines = [f"Key message: {message_value}", f"Primary CTA: {cta_value}"]
    if tone_value:
        message_lines.append(f"Tone: {tone_value}")

    sections: List[BriefSection] = [
        BriefSection(title="Overview", lines=overview_lines),
        BriefSection(title="Audience", lines=[audience_value]),
        BriefSection(title="Message", lines=message_lines),
    ]

    if asset_list:
        sections.append(BriefSection(title="Assets", lines=asset_list))
    if proof_list or source_list:
        lines: List[str] = []
        if proof_list:
            lines.append("Proof points: " + "; ".join(proof_list))
        if source_list:
            lines.append("Sources: " + "; ".join(source_list))
        sections.append(BriefSection(title="Proof & Sources", lines=lines))
    if approval_list:
        sections.append(BriefSection(title="Approvals", lines=approval_list))
    if constraint_list:
        sections.append(BriefSection(title="Constraints", lines=constraint_list))

    readiness_lines = [
        f"Assets listed: {'yes' if asset_list else 'no'}",
        f"Proof points listed: {'yes' if proof_list else 'no'}",
        f"Approvals listed: {'yes' if approval_list else 'no'}",
        f"Publish date set: {'yes' if publish_value else 'no'}",
    ]
    sections.append(BriefSection(title="Readiness", lines=readiness_lines))

    brief_text_parts: List[str] = [title_value, ""]
    for section in sections:
        brief_text_parts.append(section.title)
        for line in section.lines:
            if line.startswith("-"):
                brief_text_parts.append(line)
            else:
                brief_text_parts.append(f"- {line}")
        brief_text_parts.append("")

    brief_text = "\n".join(brief_text_parts).strip()

    return {
        "title": title_value,
        "summary": f"Ready for {channel_value} publishing.",
        "sections": [
            {"title": section.title, "lines": section.lines} for section in sections
        ],
        "brief_text": brief_text,
        "sparky": "Publish brief ready. You can copy and share it.",
    }, None
