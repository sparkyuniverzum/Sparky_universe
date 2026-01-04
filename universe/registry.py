from __future__ import annotations

from importlib import metadata
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

MODULES_PATH = Path(__file__).parent.parent / "modules"
ENTRYPOINT_GROUP = "sparky.modules"
_MODULES_CACHE: Dict[str, Any] = {"ts": 0.0, "data": None}


def _modules_cache_ttl() -> float:
    raw = os.getenv("SPARKY_MODULE_CACHE_SECONDS", "5").strip()
    if not raw:
        return 0.0
    try:
        value = float(raw)
    except ValueError:
        return 0.0
    if value <= 0:
        return 0.0
    return value


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
    category = data.get("category") or "Other"

    normalized = {**data}
    normalized.update(
        {
            "name": name,
            "slug": slug,
            "mount": mount,
            "public": bool(public),
            "category": str(category),
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
            try:
                with open(manifest, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            except Exception:
                logger.exception("Failed to load module manifest: %s", manifest)
                continue
            if not isinstance(data, dict):
                logger.warning(
                    "Invalid module manifest (expected mapping): %s", manifest
                )
                continue
            normalized = _normalize_module(data, source="filesystem", path=module_dir)
            if normalized:
                modules[normalized["name"]] = normalized
            else:
                logger.warning("Module manifest missing name: %s", manifest)
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
    ttl = _modules_cache_ttl()
    now = time.time()
    if ttl > 0:
        cached = _MODULES_CACHE.get("data")
        if cached is not None and now - _MODULES_CACHE.get("ts", 0.0) < ttl:
            return dict(cached)

    modules = load_filesystem_modules()
    entrypoint_modules = load_entrypoint_modules()

    for name, data in entrypoint_modules.items():
        if name not in modules:
            modules[name] = data

    if ttl > 0:
        _MODULES_CACHE.update({"ts": now, "data": dict(modules)})
    return modules
