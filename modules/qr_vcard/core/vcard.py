from __future__ import annotations

import base64
import io
from typing import Tuple

import segno


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if len(parts) == 1:
        return "", parts[0]
    return parts[-1], " ".join(parts[:-1])


def build_vcard_payload(
    full_name: str | None,
    phone: str | None,
    email: str | None,
    company: str | None,
    title: str | None,
    website: str | None,
) -> Tuple[str | None, str | None]:
    if not full_name or not full_name.strip():
        return None, "Full name is required."

    full_name = full_name.strip()
    last, first = _split_name(full_name)

    lines = ["BEGIN:VCARD", "VERSION:3.0"]
    lines.append(f"N:{_escape(last)};{_escape(first)};;;")
    lines.append(f"FN:{_escape(full_name)}")

    if company:
        lines.append(f"ORG:{_escape(company.strip())}")
    if title:
        lines.append(f"TITLE:{_escape(title.strip())}")
    if phone:
        lines.append(f"TEL;TYPE=cell:{_escape(phone.strip())}")
    if email:
        lines.append(f"EMAIL:{_escape(email.strip())}")
    if website:
        lines.append(f"URL:{_escape(website.strip())}")

    lines.append("END:VCARD")
    return "\n".join(lines), None


def render_qr_data_url(payload: str, *, scale: int = 5) -> str:
    qr = segno.make(payload)
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=scale)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
