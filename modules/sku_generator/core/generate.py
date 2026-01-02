from __future__ import annotations

import secrets
from typing import Any, Dict, List, Tuple

ALPHANUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _clean_token(value: str | None) -> str:
    if not value:
        return ""
    cleaned = value.strip().upper().replace(" ", "")
    return cleaned


def generate_skus(
    *,
    prefix: str | None,
    category: str | None,
    start: int,
    count: int,
    width: int,
    suffix_length: int,
    separator: str,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if count <= 0 or count > 5000:
        return None, "Count must be between 1 and 5000."
    if width < 1 or width > 12:
        return None, "Width must be between 1 and 12."
    if suffix_length < 0 or suffix_length > 8:
        return None, "Suffix length must be between 0 and 8."

    prefix_token = _clean_token(prefix)
    category_token = _clean_token(category)

    skus: List[str] = []
    for idx in range(count):
        number = str(start + idx).zfill(width)
        parts = [part for part in [prefix_token, category_token, number] if part]
        sku = separator.join(parts)
        if suffix_length > 0:
            suffix = "".join(secrets.choice(ALPHANUM) for _ in range(suffix_length))
            sku = f"{sku}{separator}{suffix}"
        skus.append(sku)

    return {
        "count": len(skus),
        "prefix": prefix_token,
        "category": category_token,
        "start": start,
        "width": width,
        "suffix_length": suffix_length,
        "separator": separator,
        "skus": skus,
    }, None
