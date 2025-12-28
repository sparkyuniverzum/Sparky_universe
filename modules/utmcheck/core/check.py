from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qsl, parse_qs, urlencode, urlparse, urlunparse

REQUIRED = ["utm_source", "utm_medium", "utm_campaign"]

SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qsl(parsed.query, keep_blank_values=True)
    normalized = []
    for key, value in params:
        if key.lower().startswith("utm_"):
            normalized.append((key.lower(), value.strip()))
        else:
            normalized.append((key, value))
    normalized.sort(key=lambda item: item[0])
    query = urlencode(normalized, doseq=True)
    return urlunparse(parsed._replace(query=query))


def check_utms(raw_text: Any) -> Tuple[Dict[str, Any] | None, str | None]:
    if raw_text is None:
        return None, "Provide at least one URL."
    lines = [line.strip() for line in str(raw_text).splitlines() if line.strip()]
    if not lines:
        return None, "Provide at least one URL."

    items: List[Dict[str, Any]] = []
    valid_count = 0

    for line in lines:
        assumed_scheme = False
        url = line
        if not SCHEME_RE.match(url):
            url = "https://" + url
            assumed_scheme = True

        parsed = urlparse(url)
        if not parsed.netloc:
            items.append(
                {
                    "input": line,
                    "url": url,
                    "valid": False,
                    "missing": REQUIRED,
                    "warnings": ["Invalid URL."],
                    "utm": {},
                    "normalized_url": None,
                }
            )
            continue

        query = parse_qs(parsed.query, keep_blank_values=True)
        utm: Dict[str, str] = {}
        for key, values in query.items():
            if key.lower().startswith("utm_"):
                value = values[0] if values else ""
                utm[key.lower()] = value

        missing = [name for name in REQUIRED if not utm.get(name)]
        warnings: List[str] = []
        if assumed_scheme:
            warnings.append("Added https:// for parsing.")

        for key, value in utm.items():
            if value.strip() != value:
                warnings.append(f"Trim whitespace in {key}.")
            if value and value.lower() != value:
                warnings.append(f"Use lowercase for {key}.")

        normalized_url = _normalize_url(url)
        valid = not missing
        if valid:
            valid_count += 1

        items.append(
            {
                "input": line,
                "url": url,
                "valid": valid,
                "missing": missing,
                "warnings": warnings,
                "utm": utm,
                "normalized_url": normalized_url,
            }
        )

    return {
        "total": len(items),
        "valid": valid_count,
        "items": items,
    }, None
