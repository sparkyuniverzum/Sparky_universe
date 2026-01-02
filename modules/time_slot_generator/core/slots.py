from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _parse_time(raw: str) -> Tuple[int | None, str | None]:
    if not raw or ":" not in raw:
        return None, "Time must be HH:MM."
    parts = raw.split(":")
    if len(parts) != 2:
        return None, "Time must be HH:MM."
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return None, "Time must be HH:MM."
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None, "Time must be HH:MM."
    return hour * 60 + minute, None


def _format_time(minutes: int) -> str:
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def generate_slots(
    start_time: str | None,
    end_time: str | None,
    interval_minutes: int,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if interval_minutes <= 0:
        return None, "Interval must be greater than zero."

    start, error = _parse_time(start_time or "")
    if error:
        return None, error
    end, error = _parse_time(end_time or "")
    if error:
        return None, error
    assert start is not None and end is not None

    if end <= start:
        return None, "End time must be after start time."

    slots: List[Dict[str, str]] = []
    current = start
    while current + interval_minutes <= end:
        slot_end = current + interval_minutes
        slots.append(
            {
                "start": _format_time(current),
                "end": _format_time(slot_end),
                "label": f"{_format_time(current)}-{_format_time(slot_end)}",
            }
        )
        current = slot_end

    return {
        "count": len(slots),
        "interval_minutes": interval_minutes,
        "slots": slots,
    }, None
