from __future__ import annotations

import os
from typing import Any, Dict

DEFAULT_SLOT_ORDER = ["inline", "footer"]
SLOT_DEFS: Dict[str, Dict[str, str]] = {
    "inline": {
        "label": "Sponsored",
        "position": "after_result",
        "size": "responsive",
    },
    "footer": {
        "label": "Sponsored",
        "position": "footer",
        "size": "responsive",
    },
}

PAGE_TYPE_LIMITS = {
    "tool": 2,
    "generator": 2,
    "low_content": 1,
    "index": 0,
}


def _flag(name: str, default: str = "off") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def ads_enabled() -> bool:
    return _flag("SPARKY_ADS", "off")


def ads_preview_enabled() -> bool:
    return _flag("SPARKY_ADS_PREVIEW", "on")


def _slot_enabled(slot: str) -> bool:
    env_name = f"SPARKY_ADS_{slot.upper()}"
    return _flag(env_name, "on")


def get_ads_config(page_type: str = "tool") -> Dict[str, Any]:
    enabled = ads_enabled()
    preview = ads_preview_enabled()
    max_slots = PAGE_TYPE_LIMITS.get(page_type, PAGE_TYPE_LIMITS["tool"])

    slots: Dict[str, Dict[str, Any]] = {}
    used = 0
    for slot in DEFAULT_SLOT_ORDER:
        slot_allowed = used < max_slots
        if slot_allowed:
            used += 1
        slot_on = enabled and _slot_enabled(slot) and slot_allowed

        meta = SLOT_DEFS.get(slot, {})
        slots[slot] = {
            "slot": slot,
            "label": meta.get("label", "Sponsored"),
            "position": meta.get("position", ""),
            "size": meta.get("size", "responsive"),
            "enabled": bool(slot_on),
            "allowed": bool(slot_allowed),
            "preview": bool(preview),
            "page_type": page_type,
        }

    return {
        "enabled": bool(enabled),
        "preview": bool(preview),
        "page_type": page_type,
        "max_slots": max_slots,
        "slots": slots,
    }


def attach_ads_globals(templates: Any) -> None:
    templates.env.globals.setdefault("ads_config", get_ads_config)
