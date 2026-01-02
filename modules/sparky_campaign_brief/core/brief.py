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


def _build_sections(
    *,
    name: str,
    objective: str,
    deadline: str,
    success_metric: str,
    target: str,
    audience: str,
    offer: str,
    key_message: str,
    tone: str,
    cta: str,
    channels: List[str],
    deliverables: List[str],
    proof_points: List[str],
    constraints: List[str],
    budget: str,
) -> List[BriefSection]:
    overview_lines = [f"Objective: {objective}", f"Deadline: {deadline}", f"Success metric: {success_metric} ({target})"]
    if budget:
        overview_lines.append(f"Budget: {budget}")

    audience_lines = [audience]

    offer_lines = [offer]
    if proof_points:
        offer_lines.append("Proof points: " + "; ".join(proof_points))

    message_lines = [f"Core message: {key_message}", f"Primary CTA: {cta}"]
    if tone:
        message_lines.append(f"Tone: {tone}")

    channel_lines = channels
    deliverable_lines = deliverables

    sections = [
        BriefSection(title="Overview", lines=overview_lines),
        BriefSection(title="Audience", lines=audience_lines),
        BriefSection(title="Offer", lines=offer_lines),
        BriefSection(title="Message", lines=message_lines),
        BriefSection(title="Channels", lines=channel_lines),
        BriefSection(title="Deliverables", lines=deliverable_lines),
    ]

    if constraints:
        sections.append(BriefSection(title="Constraints", lines=constraints))

    return sections


def build_campaign_brief(
    *,
    campaign_name: str | None,
    objective: str | None,
    deadline: str | None,
    success_metric: str | None,
    target: str | None,
    audience: str | None,
    offer: str | None,
    key_message: str | None,
    tone: str | None,
    cta: str | None,
    channels: str | None,
    deliverables: str | None,
    proof_points: str | None,
    constraints: str | None,
    budget: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    objective_value, error = _require(objective, "Objective")
    if error:
        return None, error
    deadline_value, error = _require(deadline, "Deadline")
    if error:
        return None, error
    success_value, error = _require(success_metric, "Success metric")
    if error:
        return None, error
    target_value, error = _require(target, "Target")
    if error:
        return None, error
    audience_value, error = _require(audience, "Audience")
    if error:
        return None, error
    offer_value, error = _require(offer, "Offer")
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

    name_value = _optional(campaign_name) or "Campaign Brief"
    tone_value = _optional(tone)
    budget_value = _optional(budget)
    proof_list = _split_lines(proof_points)
    constraint_list = _split_lines(constraints)

    sections = _build_sections(
        name=name_value,
        objective=objective_value,
        deadline=deadline_value,
        success_metric=success_value,
        target=target_value,
        audience=audience_value,
        offer=offer_value,
        key_message=message_value,
        tone=tone_value,
        cta=cta_value,
        channels=channel_list,
        deliverables=deliverable_list,
        proof_points=proof_list,
        constraints=constraint_list,
        budget=budget_value,
    )

    brief_text_parts: List[str] = [name_value, ""]
    for section in sections:
        if section.title:
            brief_text_parts.append(section.title)
        for line in section.lines:
            brief_text_parts.append(f"- {line}")
        brief_text_parts.append("")

    brief_text = "\n".join(brief_text_parts).strip()
    summary = f"Brief ready: {objective_value}."

    return {
        "title": name_value,
        "summary": summary,
        "sections": [
            {"title": section.title, "lines": section.lines} for section in sections
        ],
        "brief_text": brief_text,
        "sparky": "Brief ready. You can copy and share it.",
    }, None
