from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from modules.qrverify.core.decode import decode_input


def decode_payload(
    file_bytes: bytes | None,
    payload: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    decoded, error = decode_input(file_bytes, payload)
    if error:
        return None, error

    result: Dict[str, Any] = {"decoded": decoded}
    if decoded:
        try:
            result["json"] = json.loads(decoded)
        except json.JSONDecodeError:
            pass

    return result, None
