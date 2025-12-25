import json
import segno
from typing import Dict


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
