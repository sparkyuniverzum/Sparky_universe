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


def build_data_intake_brief(
    *,
    dataset_name: str | None,
    purpose: str | None,
    source_system: str | None,
    data_format: str | None,
    refresh_cadence: str | None,
    delivery_method: str | None,
    deadline: str | None,
    volume_estimate: str | None,
    included_entities: str | None,
    exclusions: str | None,
    key_fields: str | None,
    identifiers: str | None,
    time_fields: str | None,
    transformations: str | None,
    quality_risks: str | None,
    missing_rules: str | None,
    access_constraints: str | None,
    privacy_notes: str | None,
    next_action: str | None,
    owner: str | None,
    contact: str | None,
    notes: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    purpose_value, error = _require(purpose, "Purpose")
    if error:
        return None, error
    source_value, error = _require(source_system, "Source system")
    if error:
        return None, error
    format_value, error = _require(data_format, "Data format")
    if error:
        return None, error
    cadence_value, error = _require(refresh_cadence, "Refresh cadence")
    if error:
        return None, error
    delivery_value, error = _require(delivery_method, "Delivery method")
    if error:
        return None, error
    entities_list = _split_lines(included_entities)
    if not entities_list:
        return None, "Included entities are required."
    fields_list = _split_lines(key_fields)
    if not fields_list:
        return None, "Key fields are required."
    id_list = _split_lines(identifiers)
    if not id_list:
        return None, "Identifiers are required."
    transform_list = _split_lines(transformations)
    if not transform_list:
        return None, "Transformations are required."
    action_value, error = _require(next_action, "Next action")
    if error:
        return None, error

    title_value = _optional(dataset_name) or "Data Intake Brief"
    deadline_value = _optional(deadline)
    volume_value = _optional(volume_estimate)
    exclusion_list = _split_lines(exclusions)
    time_list = _split_lines(time_fields)
    risk_list = _split_lines(quality_risks)
    missing_list = _split_lines(missing_rules)
    access_list = _split_lines(access_constraints)
    privacy_value = _optional(privacy_notes)
    owner_value = _optional(owner)
    contact_value = _optional(contact)
    notes_value = _optional(notes)

    overview_lines = [
        f"Purpose: {purpose_value}",
        f"Source system: {source_value}",
        f"Format: {format_value}",
        f"Refresh cadence: {cadence_value}",
        f"Delivery method: {delivery_value}",
    ]
    if deadline_value:
        overview_lines.append(f"Deadline: {deadline_value}")
    if volume_value:
        overview_lines.append(f"Volume estimate: {volume_value}")
    if owner_value:
        overview_lines.append(f"Owner: {owner_value}")

    scope_lines = ["Included: " + "; ".join(entities_list)]
    if exclusion_list:
        scope_lines.append("Excluded: " + "; ".join(exclusion_list))

    schema_lines = [
        "Key fields: " + "; ".join(fields_list),
        "Identifiers: " + "; ".join(id_list),
    ]
    if time_list:
        schema_lines.append("Time fields: " + "; ".join(time_list))

    transformation_lines = transform_list

    quality_lines: List[str] = []
    if risk_list:
        quality_lines.append("Known risks: " + "; ".join(risk_list))
    if missing_list:
        quality_lines.append("Missing data rules: " + "; ".join(missing_list))

    access_lines: List[str] = []
    if access_list:
        access_lines.append("Access constraints: " + "; ".join(access_list))
    if privacy_value:
        access_lines.append(f"Privacy notes: {privacy_value}")

    handoff_lines = [f"Next action: {action_value}"]
    if contact_value:
        handoff_lines.append(f"Contact: {contact_value}")
    if notes_value:
        handoff_lines.append(f"Notes: {notes_value}")

    sections: List[BriefSection] = [
        BriefSection(title="Overview", lines=overview_lines),
        BriefSection(title="Scope", lines=scope_lines),
        BriefSection(title="Schema", lines=schema_lines),
        BriefSection(title="Transformations", lines=transformation_lines),
    ]

    if quality_lines:
        sections.append(BriefSection(title="Quality", lines=quality_lines))
    if access_lines:
        sections.append(BriefSection(title="Access & Privacy", lines=access_lines))

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
        "summary": "Intake brief ready for handoff.",
        "sections": [
            {"title": section.title, "lines": section.lines} for section in sections
        ],
        "brief_text": brief_text,
        "sparky": "Intake brief ready. You can copy and share it.",
    }, None
