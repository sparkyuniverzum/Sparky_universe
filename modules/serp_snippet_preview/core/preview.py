from __future__ import annotations

from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def preview_snippet(
    *,
    title: str | None,
    description: str | None,
    url: str | None,
) -> Tuple[Dict[str, Any], List[str]]:
    title = (title or "").strip()
    description = (description or "").strip()
    url = (url or "").strip()

    warnings: List[str] = []

    title_len = len(title)
    desc_len = len(description)

    if title_len and not (50 <= title_len <= 60):
        warnings.append("Title length should be 50-60 characters.")
    if desc_len and not (120 <= desc_len <= 160):
        warnings.append("Description length should be 120-160 characters.")
    if url and not _valid_url(url):
        warnings.append("URL should include scheme and domain.")

    host = ""
    path = ""
    if url and _valid_url(url):
        parsed = urlparse(url)
        host = parsed.netloc
        path = parsed.path or "/"
    elif url:
        host = url

    return {
        "title": title,
        "description": description,
        "url": url,
        "host": host,
        "path": path,
        "lengths": {"title": title_len, "description": desc_len},
    }, warnings
