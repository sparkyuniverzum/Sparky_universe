from __future__ import annotations

import base64
import binascii
from typing import Tuple

try:
    import cv2
    import numpy as np
except Exception:  # pragma: no cover - optional dependency guard
    cv2 = None
    np = None


def _decode_data_url(data_url: str) -> Tuple[bytes | None, str | None]:
    if not data_url.startswith("data:"):
        return None, None

    try:
        header, b64 = data_url.split(",", 1)
    except ValueError:
        return None, "Invalid data URL format."

    if ";base64" not in header:
        return None, "Data URL must be base64 encoded."

    try:
        return base64.b64decode(b64, validate=True), None
    except binascii.Error:
        return None, "Invalid base64 payload."


def _decode_qr_cv2(image_bytes: bytes) -> str | None:
    if cv2 is None or np is None:
        return None

    data = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        return None

    detector = cv2.QRCodeDetector()
    decoded, _, _ = detector.detectAndDecode(image)
    return decoded or None


def decode_input(
    file_bytes: bytes | None,
    payload: str | None,
) -> Tuple[str | None, str | None]:
    if payload:
        payload = payload.strip()
        if payload:
            data_bytes, error = _decode_data_url(payload)
            if error:
                return None, error
            if data_bytes is not None:
                if cv2 is None or np is None:
                    return None, "QR decoding is unavailable; install opencv-python-headless."
                decoded = _decode_qr_cv2(data_bytes)
                if not decoded:
                    return None, "Could not decode QR from data URL."
                return decoded, None
            return payload, None

    if file_bytes:
        if cv2 is None or np is None:
            return None, "QR decoding is unavailable; install opencv-python-headless."
        decoded = _decode_qr_cv2(file_bytes)
        if not decoded:
            return None, "Could not decode QR from image."
        return decoded, None

    if cv2 is None or np is None:
        return None, "QR decoding is unavailable; install opencv-python-headless."

    return None, "Provide a QR image or payload to verify."
