from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from modules.qrforge.core.verify import verify_payload_signature


def extract_signed_payload(decoded: str) -> Tuple[Dict[str, Any] | None, str | None]:
    try:
        data = json.loads(decoded)
    except json.JSONDecodeError:
        return None, None

    if not isinstance(data, dict):
        return None, None

    payload = data.get("payload")
    signature = data.get("signature")

    if isinstance(payload, dict) and isinstance(signature, str):
        return payload, signature

    return None, None


def verify_signature(payload: Dict[str, Any], signature: str, secret: str) -> bool:
    return verify_payload_signature(payload, signature, secret)
