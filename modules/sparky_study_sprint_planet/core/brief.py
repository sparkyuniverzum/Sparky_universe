from __future__ import annotations

import math
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


def _parse_topics(text: str | None) -> List[Dict[str, Any]]:
    topics: List[Dict[str, Any]] = []
    for line in _split_lines(text):
        parts = [part.strip() for part in line.split("|")]
        name = parts[0] if parts else ""
        if not name:
            continue
        priority = 2
        difficulty = 2
        if len(parts) > 1 and parts[1].isdigit():
            priority = max(1, min(int(parts[1]), 3))
        if len(parts) > 2 and parts[2].isdigit():
            difficulty = max(1, min(int(parts[2]), 3))
        weight = priority * difficulty
        topics.append(
            {
                "name": name,
                "priority": priority,
                "difficulty": difficulty,
                "weight": weight,
            }
        )
    return topics


def _allocate_sessions(topics: List[Dict[str, Any]], total_sessions: int) -> Dict[str, int]:
    if not topics:
        return {}
    total_weight = sum(topic["weight"] for topic in topics) or 1
    allocations: List[Tuple[str, int, float]] = []
    base_total = 0
    for topic in topics:
        raw = (total_sessions * topic["weight"]) / total_weight
        base = int(math.floor(raw))
        base_total += base
        allocations.append((topic["name"], base, raw - base))

    remaining = total_sessions - base_total
    allocations.sort(key=lambda item: item[2], reverse=True)
    counts: Dict[str, int] = {name: base for name, base, _ in allocations}
    idx = 0
    while remaining > 0 and allocations:
        name, base, _ = allocations[idx % len(allocations)]
        counts[name] += 1
        remaining -= 1
        idx += 1
    return counts


def _build_learn_queue(counts: Dict[str, int]) -> List[str]:
    queue: List[str] = []
    pool = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    remaining = {name: count for name, count in pool}
    while any(count > 0 for count in remaining.values()):
        for name, _ in pool:
            if remaining[name] > 0:
                queue.append(name)
                remaining[name] -= 1
    return queue


def build_sprint_plan(
    *,
    goal: str | None,
    days: str | None,
    minutes_per_day: str | None,
    session_length: str | None,
    buffer_days: str | None,
    review_blocks_per_day: str | None,
    topics: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    goal_value, error = _require(goal, "Goal")
    if error:
        return None, error
    days_value, error = _parse_int(days, "Days", 2)
    if error:
        return None, error
    minutes_value, error = _parse_int(minutes_per_day, "Minutes per day", 20)
    if error:
        return None, error

    session_value = 25
    if session_length and str(session_length).strip():
        session_value, error = _parse_int(session_length, "Session length", 15)
        if error:
            return None, error

    buffer_value = 0
    if buffer_days and str(buffer_days).strip():
        buffer_value, error = _parse_int(buffer_days, "Buffer days", 0)
        if error:
            return None, error

    review_value = 1
    if review_blocks_per_day and str(review_blocks_per_day).strip():
        review_value, error = _parse_int(
            review_blocks_per_day, "Review blocks per day", 0
        )
        if error:
            return None, error

    topics_value = _parse_topics(topics)
    if not topics_value:
        return None, "Topics are required."

    sessions_per_day = max(1, minutes_value // session_value)
    buffer_value = min(buffer_value, max(days_value - 1, 0))
    active_days = max(days_value - buffer_value, 1)

    review_per_day = min(review_value, max(sessions_per_day - 1, 0))
    review_sessions = review_per_day * max(active_days - 1, 0)
    total_sessions = sessions_per_day * active_days
    learn_sessions = max(total_sessions - review_sessions, 0)

    counts = _allocate_sessions(topics_value, learn_sessions)
    learn_queue = _build_learn_queue(counts)

    learned_topics: List[str] = []
    schedule: List[str] = []
    review_index = 0
    learn_index = 0

    for day in range(1, active_days + 1):
        day_items: List[str] = []
        review_slots = review_per_day if day > 1 else 0
        learn_slots = sessions_per_day - review_slots

        for _ in range(learn_slots):
            if learn_index < len(learn_queue):
                topic = learn_queue[learn_index]
                learn_index += 1
            else:
                topic = learned_topics[review_index % len(learned_topics)] if learned_topics else "Review"
            day_items.append(f"Learn — {topic}")
            if topic not in learned_topics:
                learned_topics.append(topic)

        for _ in range(review_slots):
            if learned_topics:
                topic = learned_topics[review_index % len(learned_topics)]
                review_index += 1
                day_items.append(f"Review — {topic}")
            else:
                day_items.append("Review — (first learn)")

        schedule.append(f"Day {day}: " + " | ".join(day_items))

    for day in range(active_days + 1, days_value + 1):
        schedule.append(f"Day {day}: Buffer / catch-up / rest")

    milestone_day = max(1, active_days // 2)
    milestones = [
        f"Checkpoint day: {milestone_day}",
        f"Final review day: {active_days}",
    ]

    overview_lines = [
        f"Goal: {goal_value}",
        f"Total days: {days_value}",
        f"Active days: {active_days}",
        f"Buffer days: {buffer_value}",
        f"Minutes per day: {minutes_value}",
        f"Session length: {session_value}",
        f"Sessions per day: {sessions_per_day}",
        f"Learning sessions: {learn_sessions}",
        f"Review sessions: {review_sessions}",
    ]

    topic_lines = [
        f"{topic['name']} (priority {topic['priority']}, difficulty {topic['difficulty']})"
        for topic in topics_value
    ]

    allocation_lines = [f"{name}: {count} sessions" for name, count in counts.items()]

    sections = [
        BriefSection(title="Overview", lines=overview_lines),
        BriefSection(title="Topics", lines=topic_lines),
        BriefSection(title="Session allocation", lines=allocation_lines),
        BriefSection(title="Milestones", lines=milestones),
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
