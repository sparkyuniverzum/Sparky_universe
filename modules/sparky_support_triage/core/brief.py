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


def build_triage_brief(
    *,
    issue_title: str | None,
    reported_by: str | None,
    report_time: str | None,
    severity: str | None,
    impact_scope: str | None,
    user_impact: str | None,
    affected_product: str | None,
    environment: str | None,
    symptoms: str | None,
    reproduction: str | None,
    recent_changes: str | None,
    logs: str | None,
    workarounds: str | None,
    owner: str | None,
    next_action: str | None,
    comms_plan: str | None,
    constraints: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    title_value, error = _require(issue_title, "Issue title")
    if error:
        return None, error
    reported_value, error = _require(reported_by, "Reported by")
    if error:
        return None, error
    time_value, error = _require(report_time, "Report time")
    if error:
        return None, error
    severity_value, error = _require(severity, "Severity")
    if error:
        return None, error
    impact_value, error = _require(impact_scope, "Impact scope")
    if error:
        return None, error
    user_value, error = _require(user_impact, "User impact")
    if error:
        return None, error
    product_value, error = _require(affected_product, "Affected product")
    if error:
        return None, error
    env_value, error = _require(environment, "Environment")
    if error:
        return None, error

    symptom_list = _split_lines(symptoms)
    if not symptom_list:
        return None, "Symptoms are required."

    repro_value = _optional(reproduction)
    change_list = _split_lines(recent_changes)
    log_list = _split_lines(logs)
    workaround_list = _split_lines(workarounds)
    owner_value = _optional(owner)
    action_value, error = _require(next_action, "Next action")
    if error:
        return None, error
    comms_value = _optional(comms_plan)
    constraint_list = _split_lines(constraints)

    overview_lines = [
        f"Reported by: {reported_value}",
        f"Report time: {time_value}",
        f"Severity: {severity_value}",
        f"Impact scope: {impact_value}",
    ]

    impact_lines = [
        f"User impact: {user_value}",
        f"Affected product: {product_value}",
        f"Environment: {env_value}",
    ]

    sections: List[BriefSection] = [
        BriefSection(title="Overview", lines=overview_lines),
        BriefSection(title="Impact", lines=impact_lines),
        BriefSection(title="Symptoms", lines=symptom_list),
    ]

    if repro_value:
        sections.append(BriefSection(title="Reproduction", lines=[repro_value]))
    if change_list:
        sections.append(BriefSection(title="Recent changes", lines=change_list))
    if log_list:
        sections.append(BriefSection(title="Logs & evidence", lines=log_list))
    if workaround_list:
        sections.append(BriefSection(title="Workarounds", lines=workaround_list))

    handoff_lines = [f"Next action: {action_value}"]
    if owner_value:
        handoff_lines.append(f"Owner: {owner_value}")
    if comms_value:
        handoff_lines.append(f"Comms plan: {comms_value}")
    if constraint_list:
        handoff_lines.append("Constraints: " + "; ".join(constraint_list))

    sections.append(BriefSection(title="Handoff", lines=handoff_lines))

    brief_text_parts: List[str] = [title_value, ""]
    for section in sections:
        brief_text_parts.append(section.title)
        for line in section.lines:
            brief_text_parts.append(f"- {line}")
        brief_text_parts.append("")

    brief_text = "\n".join(brief_text_parts).strip()

    return {
        "title": title_value,
        "summary": "Triage brief ready for response.",
        "sections": [
            {"title": section.title, "lines": section.lines} for section in sections
        ],
        "brief_text": brief_text,
        "sparky": "Triage brief ready. You can copy and share it.",
    }, None
