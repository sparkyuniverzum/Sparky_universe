from __future__ import annotations

from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def _ratio(width: int | None, height: int | None) -> float | None:
    if not width or not height:
        return None
    if width <= 0 or height <= 0:
        return None
    return round(width / height, 2)


def validate_preview(
    *,
    title: str | None,
    description: str | None,
    url: str | None,
    image_url: str | None,
    site_name: str | None,
    twitter_handle: str | None,
    image_width: int | None,
    image_height: int | None,
    card_type: str | None,
) -> Tuple[Dict[str, Any], List[str]]:
    title = (title or "").strip()
    description = (description or "").strip()
    url = (url or "").strip()
    image_url = (image_url or "").strip()
    site_name = (site_name or "").strip()
    twitter_handle = (twitter_handle or "").strip()
    card_type = (card_type or "summary_large_image").strip()

    warnings: List[str] = []

    title_len = len(title)
    desc_len = len(description)

    if title_len and not (30 <= title_len <= 60):
        warnings.append("Title length should be 30-60 characters.")
    if desc_len and not (55 <= desc_len <= 160):
        warnings.append("Description length should be 55-160 characters.")
    if url and not _valid_url(url):
        warnings.append("URL should include scheme and domain.")
    if twitter_handle and not twitter_handle.startswith("@"):
        warnings.append("Twitter handle should start with @.")

    ratio = _ratio(image_width, image_height)
    if card_type == "summary":
        min_ratio, max_ratio = 0.9, 1.1
        target_ratio = 1.0
    else:
        min_ratio, max_ratio = 1.7, 2.1
        target_ratio = 1.91

    if ratio is not None and not (min_ratio <= ratio <= max_ratio):
        warnings.append(
            f"Image ratio should be about {target_ratio}:1 for {card_type} cards."
        )

    if image_width and image_height:
        if image_width < 600 or image_height < 315:
            warnings.append("Image is smaller than 600x315 (may look blurry).")
        elif image_width < 1200 or image_height < 630:
            warnings.append("Image is below 1200x630 (recommended size).")

    return {
        "title": title,
        "description": description,
        "url": url,
        "image_url": image_url,
        "site_name": site_name,
        "twitter_handle": twitter_handle,
        "card_type": card_type,
        "lengths": {"title": title_len, "description": desc_len},
        "image": {
            "width": image_width,
            "height": image_height,
            "ratio": ratio,
        },
    }, warnings
