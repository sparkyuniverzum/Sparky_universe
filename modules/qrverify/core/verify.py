from __future__ import annotations

from typing import Any, Dict

from .signature import extract_signed_payload, verify_signature


def verify_decoded(
    decoded: str,
    secret: str,
    forge_url: str | None = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "valid": False,
        "issuer": "custom",
        "decoded": decoded,
        "signature": "missing",
        "signature_value": None,
        "timestamp": None,
        "forge_url": None,
    }

    payload, signature = extract_signed_payload(decoded)
    if payload is None or signature is None:
        return result

    result["signature_value"] = signature
    result["payload"] = payload
    result["timestamp"] = payload.get("timestamp") if isinstance(payload, dict) else None

    if verify_signature(payload, signature, secret):
        result["valid"] = True
        result["issuer"] = "sparky"
        result["signature"] = "ok"
        if forge_url:
            result["forge_url"] = forge_url
    else:
        result["signature"] = "invalid"

    return result
