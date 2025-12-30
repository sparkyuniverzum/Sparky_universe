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
        .replace(":", "\\:")
    )


def build_wifi_payload(
    ssid: str | None,
    password: str | None,
    security: str | None,
    hidden: bool,
) -> Tuple[str | None, str | None]:
    if not ssid or not ssid.strip():
        return None, "SSID is required."

    ssid = ssid.strip()
    password = (password or "").strip()
    security = (security or "WPA").strip().upper()

    if security not in {"WPA", "WEP", "NOPASS"}:
        return None, "Security must be WPA, WEP, or nopass."

    if security != "NOPASS" and not password:
        return None, "Password is required for secured networks."

    if security == "NOPASS":
        password = ""

    parts = [
        "WIFI:",
        f"T:{security if security != 'NOPASS' else 'nopass'};",
        f"S:{_escape(ssid)};",
        f"P:{_escape(password)};",
    ]
    if hidden:
        parts.append("H:true;")
    parts.append(";")
    return "".join(parts), None


def render_qr_data_url(payload: str, *, scale: int = 5) -> str:
    qr = segno.make(payload)
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=scale)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
