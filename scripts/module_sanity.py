#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import yaml


def _mount_from(name: str, raw: str | None) -> str:
    mount = raw or f"/{name.replace('_', '-')}"
    if not mount.startswith("/"):
        mount = "/" + mount
    if mount != "/" and mount.endswith("/"):
        mount = mount.rstrip("/")
    return mount


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    modules_dir = root / "modules"
    errors: list[str] = []
    mounts: dict[str, str] = {}
    names: set[str] = set()

    for module_dir in sorted(modules_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        manifest = module_dir / "module.yaml"
        if not manifest.exists():
            continue
        try:
            data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            errors.append(f"{module_dir.name}: invalid YAML ({exc})")
            continue

        name = str(data.get("name") or "").strip() or module_dir.name
        if name in names:
            errors.append(f"{module_dir.name}: duplicate name '{name}'")
        else:
            names.add(name)

        title = str(data.get("title") or "").strip()
        description = str(data.get("description") or "").strip()
        category = str(data.get("category") or "").strip()
        public = data.get("public")
        if public is None:
            public = True

        if not title:
            errors.append(f"{module_dir.name}: missing title")
        if not description:
            errors.append(f"{module_dir.name}: missing description")
        if not category:
            errors.append(f"{module_dir.name}: missing category")

        if category != "Internal":
            standard_version = str(data.get("standard_version") or "").strip()
            if standard_version != "1.0":
                errors.append(
                    f"{module_dir.name}: standard_version must be '1.0'"
                )

        entrypoints = data.get("entrypoints") or {}
        api = entrypoints.get("api") if isinstance(entrypoints, dict) else None
        if public:
            if not api:
                errors.append(f"{module_dir.name}: missing entrypoints.api")
            elif ":" not in str(api):
                errors.append(f"{module_dir.name}: entrypoints.api must be module:app")

        mount = _mount_from(name, data.get("mount") if isinstance(data, dict) else None)
        if mount == "/":
            errors.append(f"{module_dir.name}: mount '/' is reserved")
        if " " in mount:
            errors.append(f"{module_dir.name}: mount contains spaces")
        if mount in mounts:
            errors.append(
                f"{module_dir.name}: mount '{mount}' duplicates {mounts[mount]}"
            )
        else:
            mounts[mount] = name

    if errors:
        print("Module sanity check failed:\n")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("Module sanity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
