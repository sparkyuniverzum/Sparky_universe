#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import yaml

from universe.lint import lint_module


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    modules_dir = root / "modules"
    issues = 0
    for module_dir in sorted(modules_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        manifest = module_dir / "module.yaml"
        if not manifest.exists():
            continue
        try:
            data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
        meta = {
            "name": data.get("name", module_dir.name),
            "path": module_dir,
            "public": data.get("public", True),
        }
        lint = lint_module(meta)
        if lint["ok"]:
            continue
        issues += 1
        print(f"[ERROR] {module_dir.name}")
        for issue in lint.get("issues", []):
            print(f"  - {issue}")
        if not lint.get("entrypoint_ok", True):
            print(f"  - entrypoint: {lint.get('entrypoint_error')}")
    if issues:
        print(f"\\nFound {issues} module(s) with lint errors.")
        return 1
    print("All modules passed lint.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
