from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Dict

import yaml


def _import_attr(path: str) -> Any:
    if ":" not in path:
        raise ValueError("Invalid entrypoint; expected module:attr")
    module_path, attr = path.split(":", 1)
    module = import_module(module_path)
    return getattr(module, attr)


def lint_module(meta: Dict[str, Any]) -> Dict[str, Any]:
    issues: list[str] = []
    manifest_data: Dict[str, Any] = {}

    path = meta.get("path")
    if path is None and meta.get("name"):
        path = Path(__file__).parent.parent / "modules" / meta["name"]
    elif isinstance(path, str):
        path = Path(path)

    manifest_path = None
    if isinstance(path, Path):
        manifest_path = path / "module.yaml"

    if not manifest_path or not manifest_path.exists():
        issues.append("missing module.yaml")
    else:
        try:
            manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            issues.append(f"invalid module.yaml: {exc}")
            manifest_data = {}

    if not isinstance(manifest_data, dict):
        issues.append("module.yaml must be a mapping")
        manifest_data = {}

    public = manifest_data.get("public")
    if public is None:
        public = meta.get("public", True)

    required_fields = ["name", "title", "version", "description", "public", "category"]
    if public:
        required_fields.extend(["entrypoints", "mount"])

    for field in required_fields:
        if field not in manifest_data:
            issues.append(f"missing field: {field}")
            continue
        value = manifest_data.get(field)
        if value is None:
            issues.append(f"missing field: {field}")
        elif isinstance(value, str) and not value.strip():
            issues.append(f"missing field: {field}")

    if public:
        mount_value = manifest_data.get("mount")
        if mount_value is not None:
            if not isinstance(mount_value, str):
                issues.append("mount must be a string")
            else:
                mount_value = mount_value.strip()
                if mount_value:
                    if not mount_value.startswith("/"):
                        issues.append("mount must start with /")
                    if mount_value != "/" and mount_value.endswith("/"):
                        issues.append("mount must not end with /")
                    if "://" in mount_value or mount_value.startswith("//") or "\\" in mount_value:
                        issues.append("mount must be a path")

    entrypoint = ""
    entrypoint_ok = True
    entrypoint_error = ""
    entrypoints = manifest_data.get("entrypoints")
    if public:
        if not isinstance(entrypoints, dict):
            entrypoint_ok = False
            entrypoint_error = "missing entrypoints.api"
        else:
            entrypoint = str(entrypoints.get("api") or "")
            if not entrypoint:
                entrypoint_ok = False
                entrypoint_error = "missing entrypoints.api"
    elif isinstance(entrypoints, dict):
        entrypoint = str(entrypoints.get("api") or "")

    if entrypoint:
        if ":" not in entrypoint:
            entrypoint_ok = False
            entrypoint_error = "invalid entrypoint format"
        else:
            try:
                _import_attr(entrypoint)
            except Exception as exc:
                entrypoint_ok = False
                entrypoint_error = str(exc)

    has_app = False
    has_template = False
    has_core = False
    if isinstance(path, Path):
        has_app = (path / "tool" / "app.py").exists()
        has_template = (path / "tool" / "templates" / "index.html").exists()
        has_core = (path / "core").exists()
        if public and not has_app:
            issues.append("missing tool/app.py")
        if public and not has_template:
            issues.append("missing tool/templates/index.html")
        if public and not has_core:
            issues.append("missing core/")

    ok = not issues and entrypoint_ok
    return {
        "ok": ok,
        "issues": issues,
        "entrypoint": entrypoint,
        "entrypoint_ok": entrypoint_ok,
        "entrypoint_error": entrypoint_error,
        "has_app": has_app,
        "has_template": has_template,
        "has_core": has_core,
        "public": bool(public),
    }
