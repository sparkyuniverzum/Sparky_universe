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


def build_launch_brief(
    *,
    launch_name: str | None,
    release_type: str | None,
    launch_date: str | None,
    objective: str | None,
    success_metric: str | None,
    target: str | None,
    audience: str | None,
    value_prop: str | None,
    key_message: str | None,
    cta: str | None,
    channels: str | None,
    deliverables: str | None,
    readiness: str | None,
    dependencies: str | None,
    risks: str | None,
    mitigations: str | None,
    owners: str | None,
    approvals: str | None,
    support_notes: str | None,
    rollback_plan: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    release_value, error = _require(release_type, "Release type")
    if error:
        return None, error
    date_value, error = _require(launch_date, "Launch date")
    if error:
        return None, error
    objective_value, error = _require(objective, "Objective")
    if error:
        return None, error
    metric_value, error = _require(success_metric, "Success metric")
    if error:
        return None, error
    target_value, error = _require(target, "Target")
    if error:
        return None, error
    audience_value, error = _require(audience, "Audience")
    if error:
        return None, error
    value_value, error = _require(value_prop, "Value proposition")
    if error:
        return None, error
    message_value, error = _require(key_message, "Key message")
    if error:
        return None, error
    cta_value, error = _require(cta, "Primary CTA")
    if error:
        return None, error

    channel_list = _split_lines(channels)
    if not channel_list:
        return None, "Channels are required."
    deliverable_list = _split_lines(deliverables)
    if not deliverable_list:
        return None, "Deliverables are required."

    readiness_list = _split_lines(readiness)
    dependency_list = _split_lines(dependencies)
    risk_list = _split_lines(risks)
    mitigation_list = _split_lines(mitigations)
    owner_list = _split_lines(owners)
    approval_list = _split_lines(approvals)

    title_value = _optional(launch_name) or "Launch Brief"
    support_value = _optional(support_notes)
    rollback_value = _optional(rollback_plan)

    overview_lines = [
        f"Release type: {release_value}",
        f"Launch date: {date_value}",
        f"Objective: {objective_value}",
        f"Success metric: {metric_value} ({target_value})",
    ]

    message_lines = [
        f"Value proposition: {value_value}",
        f"Key message: {message_value}",
        f"Primary CTA: {cta_value}",
    ]

    sections: List[BriefSection] = [
        BriefSection(title="Overview", lines=overview_lines),
        BriefSection(title="Audience", lines=[audience_value]),
        BriefSection(title="Message", lines=message_lines),
        BriefSection(title="Channels", lines=channel_list),
        BriefSection(title="Deliverables", lines=deliverable_list),
    ]

    if readiness_list:
        sections.append(BriefSection(title="Readiness", lines=readiness_list))
    if dependency_list:
        sections.append(BriefSection(title="Dependencies", lines=dependency_list))
    if risk_list:
        sections.append(BriefSection(title="Risks", lines=risk_list))
    if mitigation_list:
        sections.append(BriefSection(title="Mitigations", lines=mitigation_list))
    if owner_list:
        sections.append(BriefSection(title="Owners", lines=owner_list))
    if approval_list:
        sections.append(BriefSection(title="Approvals", lines=approval_list))
    if support_value:
        sections.append(BriefSection(title="Support notes", lines=[support_value]))
    if rollback_value:
        sections.append(BriefSection(title="Rollback plan", lines=[rollback_value]))

    brief_text_parts: List[str] = [title_value, ""]
    for section in sections:
        brief_text_parts.append(section.title)
        for line in section.lines:
            brief_text_parts.append(f"- {line}")
        brief_text_parts.append("")

    brief_text = "\n".join(brief_text_parts).strip()

    return {
        "title": title_value,
        "summary": "Launch brief ready for distribution.",
        "sections": [
            {"title": section.title, "lines": section.lines} for section in sections
        ],
        "brief_text": brief_text,
        "sparky": "Launch brief ready. You can copy and share it.",
    }, None
