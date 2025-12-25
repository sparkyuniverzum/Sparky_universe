import json
import hmac
import hashlib
from typing import Dict


def verify_payload_signature(
    payload: Dict,
    signature: str,
    secret: str,
) -> bool:
    """
    Verifies HMAC signature for given payload.
    """
    message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    expected = hmac.new(
        key=secret.encode(),
        msg=message,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
