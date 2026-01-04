from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from universe.seo import (
    seo_collection_json_ld,
    seo_enabled,
    seo_module_json_ld,
    seo_site_json_ld,
)

DEFAULT_SLOT_ORDER = ["inline", "footer"]
AD_CLIENT_ID = os.getenv("SPARKY_ADS_CLIENT", "ca-pub-7363912383995147").strip()
DEFAULT_SLOT_IDS = {
    "inline": "6346276219",
    "footer": "6346276219",
}
SLOT_DEFS: Dict[str, Dict[str, str]] = {
    "inline": {
        "label": "Sponsored",
        "position": "after_result",
        "size": "responsive",
        "format": "auto",
        "full_width": "true",
    },
    "footer": {
        "label": "Sponsored",
        "position": "footer",
        "size": "responsive",
        "format": "rectangle",
        "full_width": "false",
    },
}

PAGE_TYPE_LIMITS = {
    "tool": 2,
    "generator": 2,
    "low_content": 1,
    "index": 0,
}


def _slot_id(slot: str) -> str:
    env_name = f"SPARKY_ADS_SLOT_{slot.upper()}"
    value = os.getenv(env_name, "").strip()
    if value:
        return value
    return DEFAULT_SLOT_IDS.get(slot, "")


def _slot_format(slot: str, fallback: str) -> str:
    env_name = f"SPARKY_ADS_FORMAT_{slot.upper()}"
    value = os.getenv(env_name, "").strip()
    return value or fallback


def _slot_full_width(slot: str, fallback: str) -> bool:
    env_name = f"SPARKY_ADS_FULL_WIDTH_{slot.upper()}"
    value = os.getenv(env_name, "").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return fallback == "true"


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
            "client": AD_CLIENT_ID,
            "unit_id": _slot_id(slot),
            "label": meta.get("label", "Sponsored"),
            "position": meta.get("position", ""),
            "size": meta.get("size", "responsive"),
            "format": _slot_format(slot, meta.get("format", "auto")),
            "full_width": _slot_full_width(slot, meta.get("full_width", "true")),
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
    templates.env.globals.setdefault("seo_enabled", seo_enabled)
    templates.env.globals.setdefault("seo_module_json_ld", seo_module_json_ld)
    templates.env.globals.setdefault("seo_site_json_ld", seo_site_json_ld)
    templates.env.globals.setdefault("seo_collection_json_ld", seo_collection_json_ld)


def ads_txt_content(root_dir: Path | None = None) -> str | None:
    raw = os.getenv("SPARKY_ADS_TXT", "").strip()
    if not raw and root_dir is not None:
        ads_path = root_dir / "ads.txt"
        if ads_path.exists():
            raw = ads_path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    if not raw.endswith("\n"):
        raw += "\n"
    return raw
