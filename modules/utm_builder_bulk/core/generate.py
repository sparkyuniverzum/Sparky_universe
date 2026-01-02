from __future__ import annotations

from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


UTM_KEYS = [
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
]


def _split_lines(value: str | None) -> List[str]:
    if not value:
        return []
    lines: List[str] = []
    cleaned = value.replace("\r", "")
    for line in cleaned.split("\n"):
        item = line.strip()
        if item:
            lines.append(item)
    return lines


def _normalize_url(raw: str) -> str | None:
    value = raw.strip()
    if not value:
        return None
    if "://" not in value:
        value = f"https://{value}"
    return value


def build_utm_urls(
    *,
    urls_text: str | None,
    source: str | None,
    medium: str | None,
    campaign: str | None,
    term: str | None,
    content: str | None,
    keep_existing: bool,
) -> Tuple[Dict[str, Any] | None, str | None]:
    lines = _split_lines(urls_text)
    if not lines:
        return None, "Provide at least one URL."
    if len(lines) > 5000:
        return None, "Limit is 5000 URLs per request."

    utm_values = {
        "utm_source": (source or "").strip(),
        "utm_medium": (medium or "").strip(),
        "utm_campaign": (campaign or "").strip(),
        "utm_term": (term or "").strip(),
        "utm_content": (content or "").strip(),
    }

    urls: List[str] = []
    skipped: List[str] = []

    for raw in lines:
        normalized = _normalize_url(raw)
        if not normalized:
            continue
        try:
            parts = urlsplit(normalized)
        except ValueError:
            skipped.append(raw)
            continue
        if not parts.netloc:
            skipped.append(raw)
            continue

        query_items = []
        if keep_existing and parts.query:
            query_items = parse_qsl(parts.query, keep_blank_values=True)
        query_items = [
            (key, value)
            for key, value in query_items
            if key.lower() not in UTM_KEYS
        ]
        for key in UTM_KEYS:
            value = utm_values[key]
            if value:
                query_items.append((key, value))

        new_query = urlencode(query_items, doseq=True)
        new_url = urlunsplit(
            (parts.scheme, parts.netloc, parts.path, new_query, parts.fragment)
        )
        urls.append(new_url)

    if not urls:
        return None, "No valid URLs found."

    return {
        "count": len(urls),
        "utm": {key: value for key, value in utm_values.items() if value},
        "keep_existing": keep_existing,
        "urls": urls,
        "skipped": skipped,
    }, None
