from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _split_list(value: str | None) -> List[str]:
    if not value:
        return []
    items: List[str] = []
    cleaned = value.replace("\r", "").replace(",", "\n")
    for line in cleaned.split("\n"):
        item = line.strip()
        if item:
            items.append(item)
    return items


def generate_subject_variants(
    *,
    base: str | None,
    prefixes: str | None,
    suffixes: str | None,
    separator: str,
    limit: int,
) -> Tuple[Dict[str, Any] | None, str | None]:
    subject = (base or "").strip()
    if not subject:
        return None, "Provide a base subject."
    if limit <= 0 or limit > 500:
        return None, "Limit must be between 1 and 500."

    prefix_list = _split_list(prefixes)
    suffix_list = _split_list(suffixes)
    separator_text = separator or " - "

    variants: List[str] = []
    seen = set()

    def _add(value: str) -> bool:
        if value in seen:
            return False
        seen.add(value)
        variants.append(value)
        return len(variants) >= limit

    if _add(subject):
        return {"count": len(variants), "subject": subject, "variants": variants}, None

    for prefix in prefix_list:
        if _add(f"{prefix} {subject}"):
            return {"count": len(variants), "subject": subject, "variants": variants}, None

    for suffix in suffix_list:
        if _add(f"{subject}{separator_text}{suffix}"):
            return {"count": len(variants), "subject": subject, "variants": variants}, None

    for prefix in prefix_list:
        for suffix in suffix_list:
            if _add(f"{prefix} {subject}{separator_text}{suffix}"):
                return {"count": len(variants), "subject": subject, "variants": variants}, None

    return {
        "count": len(variants),
        "subject": subject,
        "variants": variants,
    }, None
