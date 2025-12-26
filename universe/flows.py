from __future__ import annotations

from typing import Any, Dict, List

from universe.registry import load_modules


def _normalize_key(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def resolve_flow_links(
    module_name: str,
    *,
    when: str = "after_success",
    base_url: str | None = None,
) -> List[Dict[str, str]]:
    modules = load_modules()
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
        href = target_meta.get("mount") or f"/{target_meta.get('slug', target_key)}"
        if base_url:
            href = base_url.rstrip("/") + href

        if not label:
            label = target_meta.get("flow_label") or target_meta.get("title") or target_key

        links.append({"label": str(label), "href": str(href)})

    return links
