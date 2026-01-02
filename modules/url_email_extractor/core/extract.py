from __future__ import annotations

import re
from typing import Any, Dict, Tuple

URL_RE = re.compile(r"(https?://[^\s<>()]+|www\.[^\s<>()]+)", re.IGNORECASE)
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)


def extract_urls_emails(text: str | None) -> Tuple[Dict[str, Any] | None, str | None]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None, "Upload a file or paste text."

    urls = URL_RE.findall(cleaned)
    emails = EMAIL_RE.findall(cleaned)

    unique_urls = sorted(set(urls))
    unique_emails = sorted(set(emails))

    return {
        "total_urls": len(urls),
        "unique_urls": len(unique_urls),
        "total_emails": len(emails),
        "unique_emails": len(unique_emails),
        "urls": unique_urls,
        "emails": unique_emails,
    }, None
