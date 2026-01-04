from __future__ import annotations

import os
from typing import Any, Dict, List

from universe.admin import get_module_overrides, module_enabled
from universe.registry import load_modules


def _normalize_key(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def _flag(name: str, default: str = "off") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _flow_fallback_enabled() -> bool:
    return _flag("SPARKY_FLOW_FALLBACK", "on")


def _flow_fallback_limit() -> int:
    raw = os.getenv("SPARKY_FLOW_FALLBACK_LIMIT", "3").strip()
    try:
        value = int(raw)
    except ValueError:
        return 3
    return max(0, value)


def _build_link(meta: Dict[str, Any], base_url: str | None) -> Dict[str, str]:
    href = meta.get("mount") or f"/{meta.get('slug', meta.get('name', ''))}"
    if base_url:
        href = base_url.rstrip("/") + href
    label = meta.get("flow_label") or meta.get("title") or meta.get("name", "Module")
    return {"label": str(label), "href": str(href)}


def _fallback_links(
    module_key: str,
    modules: Dict[str, Dict[str, Any]],
    overrides: Dict[str, bool],
    *,
    base_url: str | None,
    limit: int,
) -> List[Dict[str, str]]:
    if limit <= 0:
        return []
    source = modules.get(module_key)
    if not source:
        return []

    category = source.get("category") or "Other"
    candidates = [
        meta
        for name, meta in modules.items()
        if name != module_key
        and meta.get("public", True)
        and module_enabled(name, overrides)
    ]
    if not candidates:
        return []

    same_category = [
        meta for meta in candidates if (meta.get("category") or "Other") == category
    ]
    pool = same_category if same_category else candidates
    pool.sort(key=lambda meta: (meta.get("title") or meta.get("name", "")).lower())

    links: List[Dict[str, str]] = []
    for meta in pool[:limit]:
        links.append(_build_link(meta, base_url))
    return links


def resolve_flow_links(
    module_name: str,
    *,
    when: str = "after_success",
    base_url: str | None = None,
) -> List[Dict[str, str]]:
    modules = load_modules()
    overrides = get_module_overrides()
    name_map = {_normalize_key(name): name for name in modules.keys()}
    module_key = name_map.get(_normalize_key(module_name))
    if not module_key:
        return []

    module = modules[module_key]
    flows = (module.get("flows") or {}).get(when, [])
    links: List[Dict[str, str]] = []

    for entry in flows:
        if isinstance(entry, dict):
            target = entry.get("target") or entry.get("module") or entry.get("name")
            label = entry.get("label")
        else:
            target = entry
            label = None

        if not target:
            continue

        target_key = name_map.get(_normalize_key(str(target)))
        if not target_key:
            continue

        target_meta = modules[target_key]
        if not target_meta.get("public", True):
            continue
        if not module_enabled(target_key, overrides):
            continue
        href = target_meta.get("mount") or f"/{target_meta.get('slug', target_key)}"
        if base_url:
            href = base_url.rstrip("/") + href

        if not label:
            label = target_meta.get("flow_label") or target_meta.get("title") or target_key

        links.append({"label": str(label), "href": str(href)})

    if links or not _flow_fallback_enabled():
        return links

    return _fallback_links(
        module_key,
        modules,
        overrides,
        base_url=base_url,
        limit=_flow_fallback_limit(),
    )
