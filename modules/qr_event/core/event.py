from __future__ import annotations

import base64
import io
import uuid
from datetime import datetime, timedelta
from typing import Tuple

import segno


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _parse_datetime(value: str) -> tuple[datetime | None, str | None]:
    try:
        return datetime.fromisoformat(value), None
    except ValueError:
        return None, "Datetime must be ISO (YYYY-MM-DD or YYYY-MM-DDTHH:MM)."


def _format_datetime(value: datetime) -> str:
    return value.strftime("%Y%m%dT%H%M%S")


def build_event_payload(
    title: str | None,
    start: str | None,
    end: str | None,
    location: str | None,
    description: str | None,
) -> Tuple[str | None, str | None]:
    if not title or not title.strip():
        return None, "Title is required."
    if not start or not start.strip():
        return None, "Start time is required."

    start_value = start.strip()
    end_value = (end or "").strip()

    start_dt, error = _parse_datetime(start_value)
    if error:
        return None, error

    if end_value:
        end_dt, error = _parse_datetime(end_value)
        if error:
            return None, error
    else:
        end_dt = start_dt + timedelta(hours=1)

    if end_dt <= start_dt:
        return None, "End time must be after start time."

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Sparky Universe//QR Event//EN",
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}@sparky",
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{_format_datetime(start_dt)}",
        f"DTEND:{_format_datetime(end_dt)}",
        f"SUMMARY:{_escape(title.strip())}",
    ]

    if location:
        lines.append(f"LOCATION:{_escape(location.strip())}")
    if description:
        lines.append(f"DESCRIPTION:{_escape(description.strip())}")

    lines.extend(["END:VEVENT", "END:VCALENDAR"])
    return "\n".join(lines), None


def render_qr_data_url(payload: str, *, scale: int = 5) -> str:
    qr = segno.make(payload)
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=scale)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
