import json
import hmac
import hashlib
from typing import Dict


def sign_payload(payload: Dict, secret: str) -> str:
    """
    Creates a deterministic HMAC signature for given payload.
    """
    message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(
        key=secret.encode(),
        msg=message,
        digestmod=hashlib.sha256,
    ).hexdigest()
