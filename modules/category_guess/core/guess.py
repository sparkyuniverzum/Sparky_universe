from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Tuple


CATEGORY_KEYWORDS: dict[str, dict[str, Any]] = {
    "electronics": {
        "label": "Electronics",
        "keywords": [
            "cable",
            "adapter",
            "charger",
            "usb",
            "hdmi",
            "battery",
            "powerbank",
            "lamp",
            "projector",
            "console",
            "dock",
            "hub",
            "phone",
            "mobile",
            "tablet",
            "laptop",
            "headphone",
            "speaker",
        ],
    },
    "apparel": {
        "label": "Apparel",
        "keywords": [
            "shirt",
            "tshirt",
            "hoodie",
            "jacket",
            "dress",
            "pants",
            "jeans",
            "skirt",
            "sweater",
            "coat",
            "socks",
            "hat",
            "cap",
            "scarf",
            "shoes",
            "sneaker",
        ],
    },
    "toys": {
        "label": "Toys",
        "keywords": [
            "toy",
            "puzzle",
            "lego",
            "doll",
            "figure",
            "plush",
            "car",
            "game",
            "board game",
        ],
    },
    "accessories": {
        "label": "Accessories",
        "keywords": [
            "bag",
            "backpack",
            "wallet",
            "belt",
            "necklace",
            "bracelet",
            "ring",
            "earring",
            "case",
            "cover",
        ],
    },
    "home": {
        "label": "Home",
        "keywords": [
            "towel",
            "blanket",
            "pillow",
            "mug",
            "cup",
            "plate",
            "pan",
            "knife",
            "chair",
            "table",
            "lamp",
            "decor",
        ],
    },
    "hobby": {
        "label": "Hobby",
        "keywords": [
            "tool",
            "craft",
            "paint",
            "brush",
            "garden",
            "grill",
            "frame",
            "candle",
        ],
    },
}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    return re.sub(r"\s+", " ", normalized).strip()


def _parse_line(line: str) -> tuple[str, str | None]:
    if "|" in line:
        name, sku = line.split("|", 1)
        return name.strip(), sku.strip() or None
    if "\t" in line:
        name, sku = line.split("\t", 1)
        return name.strip(), sku.strip() or None
    return line.strip(), None


def _match_category(text: str) -> tuple[str | None, str | None]:
    for code, meta in CATEGORY_KEYWORDS.items():
        for keyword in meta["keywords"]:
            if keyword in text:
                return code, keyword
    return None, None


def guess_categories(raw_text: str | None) -> Tuple[Dict[str, Any] | None, str | None]:
    if raw_text is None or not str(raw_text).strip():
        return None, "Provide at least one product line."

    lines = [line.strip() for line in str(raw_text).splitlines() if line.strip()]
    if not lines:
        return None, "Provide at least one product line."

    items: List[Dict[str, Any]] = []
    counts: dict[str, int] = {}
    matched = 0

    for line in lines:
        name, sku = _parse_line(line)
        normalized = _normalize(" ".join([name, sku or ""]).strip())
        code, keyword = _match_category(normalized)
        label = CATEGORY_KEYWORDS.get(code or "", {}).get("label")
        if code:
            matched += 1
            counts[code] = counts.get(code, 0) + 1

        items.append(
            {
                "input": line,
                "name": name,
                "sku": sku,
                "category": code,
                "category_label": label,
                "matched_keyword": keyword,
            }
        )

    return {
        "total": len(items),
        "matched": matched,
        "categories": counts,
        "items": items,
    }, None
