from __future__ import annotations

from importlib import metadata
from pathlib import Path
from typing import Any, Dict

import yaml

MODULES_PATH = Path(__file__).parent.parent / "modules"
ENTRYPOINT_GROUP = "sparky.modules"


def _normalize_module(
    data: Dict[str, Any],
    *,
    source: str,
    path: Path | None = None,
    entry_point: str | None = None,
) -> Dict[str, Any] | None:
    name = data.get("name")
    if not name:
        return None

    slug = data.get("slug") or name.replace("_", "-")
    mount = data.get("mount") or f"/{slug}"
    public = data.get("public")
    if public is None:
        public = True

    normalized = {**data}
    normalized.update(
        {
            "name": name,
            "slug": slug,
            "mount": mount,
            "public": bool(public),
            "source": source,
        }
    )

    if path is not None:
        normalized["path"] = path
    if entry_point is not None:
        normalized["entry_point"] = entry_point

    return normalized


def load_filesystem_modules(modules_path: Path = MODULES_PATH) -> Dict[str, Dict[str, Any]]:
    modules: Dict[str, Dict[str, Any]] = {}
    if not modules_path.exists():
        return modules

    for module_dir in modules_path.iterdir():
        if not module_dir.is_dir():
            continue
        manifest = module_dir / "module.yaml"
        if manifest.exists():
            with open(manifest, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            normalized = _normalize_module(data, source="filesystem", path=module_dir)
            if normalized:
                modules[normalized["name"]] = normalized
    return modules


def load_entrypoint_modules(
    group: str = ENTRYPOINT_GROUP,
) -> Dict[str, Dict[str, Any]]:
    modules: Dict[str, Dict[str, Any]] = {}
    try:
        entry_points = metadata.entry_points()
    except Exception:
        return modules

    if hasattr(entry_points, "select"):
        selected = entry_points.select(group=group)
    else:
        selected = entry_points.get(group, [])

    for entry in selected:
        try:
            obj = entry.load()
        except Exception:
            continue

        if callable(obj):
            data = obj()
        else:
            data = obj

        if not isinstance(data, dict):
            continue

        normalized = _normalize_module(data, source="entry_point", entry_point=entry.name)
        if normalized:
            modules[normalized["name"]] = normalized

    return modules


def load_modules() -> Dict[str, Dict[str, Any]]:
    modules = load_filesystem_modules()
    entrypoint_modules = load_entrypoint_modules()

    for name, data in entrypoint_modules.items():
        if name not in modules:
            modules[name] = data

    return modules
