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


def _parse_int(value: str | None, name: str, minimum: int) -> Tuple[int | None, str | None]:
    if value is None or str(value).strip() == "":
        return None, f"{name} is required."
    try:
        parsed = int(str(value))
    except ValueError:
        return None, f"{name} must be a whole number."
    if parsed < minimum:
        return None, f"{name} must be at least {minimum}."
    return parsed, None


def _split_lines(value: str | None) -> List[str]:
    if not value:
        return []
    cleaned = value.replace("\r", "").replace(",", "\n")
    return [line.strip() for line in cleaned.split("\n") if line.strip()]


def build_sprint_plan(
    *,
    goal: str | None,
    days: str | None,
    minutes_per_day: str | None,
    session_length: str | None,
    topics: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    goal_value, error = _require(goal, "Goal")
    if error:
        return None, error
    days_value, error = _parse_int(days, "Days", 1)
    if error:
        return None, error
    minutes_value, error = _parse_int(minutes_per_day, "Minutes per day", 10)
    if error:
        return None, error

    session_value = 25
    if session_length and str(session_length).strip():
        session_value, error = _parse_int(session_length, "Session length", 10)
        if error:
            return None, error

    topic_list = _split_lines(topics)
    if not topic_list:
        return None, "Topics are required."

    sessions_per_day = max(1, minutes_value // session_value)
    total_sessions = sessions_per_day * days_value

    schedule: List[str] = []
    topic_counts = {topic: 0 for topic in topic_list}
    topic_index = 0

    for day in range(1, days_value + 1):
        day_items: List[str] = []
        for _ in range(sessions_per_day):
            topic = topic_list[topic_index]
            topic_counts[topic] += 1
            day_items.append(topic)
            topic_index = (topic_index + 1) % len(topic_list)
        day_summary = ", ".join(day_items)
        schedule.append(f"Day {day}: {day_summary}")

    overview_lines = [
        f"Goal: {goal_value}",
        f"Days: {days_value}",
        f"Minutes per day: {minutes_value}",
        f"Session length: {session_value}",
        f"Sessions per day: {sessions_per_day}",
        f"Total sessions: {total_sessions}",
    ]

    topic_lines = [f"{topic}: {count} sessions" for topic, count in topic_counts.items()]

    sections = [
        BriefSection(title="Overview", lines=overview_lines),
        BriefSection(title="Topics", lines=topic_lines),
        BriefSection(title="Schedule", lines=schedule),
    ]

    brief_text_parts: List[str] = ["Study Sprint Planet", ""]
    for section in sections:
        brief_text_parts.append(section.title)
        for line in section.lines:
            brief_text_parts.append(f"- {line}")
        brief_text_parts.append("")

    brief_text = "\n".join(brief_text_parts).strip()

    return {
        "title": "Study Sprint Planet",
        "summary": "Sprint plan ready for execution.",
        "sections": [
            {"title": section.title, "lines": section.lines} for section in sections
        ],
        "brief_text": brief_text,
        "sparky": "Sprint plan ready. You can copy and share it.",
    }, None
