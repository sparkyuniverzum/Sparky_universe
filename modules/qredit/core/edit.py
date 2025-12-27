from __future__ import annotations

import io
import json
from typing import Any, Dict, Tuple

import segno

from modules.qrverify.core.decode import decode_input


def decode_to_payload(
    file_bytes: bytes | None,
    payload: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    decoded, error = decode_input(file_bytes, payload)
    if error:
        return None, error
    if not decoded:
        return None, "No payload decoded."

    try:
        data = json.loads(decoded)
    except json.JSONDecodeError:
        return None, "Decoded payload is not JSON."

    signature = None
    if isinstance(data, dict) and "payload" in data:
        signature = data.get("signature")
        payload_value = data.get("payload")
    else:
        payload_value = data

    if not isinstance(payload_value, dict):
        return None, "Payload must be a JSON object."

    return {"payload": payload_value, "signature": signature}, None


def parse_payload_json(payload_json: str | None) -> Tuple[Dict[str, Any] | None, str | None]:
    if not payload_json or not payload_json.strip():
        return None, "Provide payload JSON."

    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError:
        return None, "Payload must be valid JSON."

    if not isinstance(payload, dict):
        return None, "Payload must be a JSON object."

    return payload, None


def render_qr_bytes(payload: Dict[str, Any], signature: str, scale: int = 5) -> bytes:
    qr_content = {
        "payload": payload,
        "signature": signature,
    }
    data = json.dumps(qr_content, sort_keys=True, separators=(",", ":"))
    qr = segno.make(data)
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=scale)
    return buffer.getvalue()
