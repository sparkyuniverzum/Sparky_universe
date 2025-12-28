import io
import json
from typing import Dict

import segno


def render_qr(
    payload: Dict,
    signature: str,
    output_path: str,
    scale: int = 5,
):
    """
    Renders a QR code containing signed payload.
    """
    qr_content = {
        "payload": payload,
        "signature": signature,
    }

    data = json.dumps(qr_content, sort_keys=True, separators=(",", ":"))
    qr = segno.make(data)
    qr.save(output_path, scale=scale)


def render_qr_bytes(
    payload: Dict,
    signature: str,
    scale: int = 5,
) -> bytes:
    """
    Renders a QR code containing signed payload into PNG bytes.
    """
    qr_content = {
        "payload": payload,
        "signature": signature,
    }
    data = json.dumps(qr_content, sort_keys=True, separators=(",", ":"))
    qr = segno.make(data)
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=scale)
    return buffer.getvalue()
