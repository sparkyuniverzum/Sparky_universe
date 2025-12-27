from __future__ import annotations

import os
from pathlib import Path


def shared_templates_dir(root_dir: Path) -> Path:
    env_path = os.getenv("SPARKY_SHARED_TEMPLATES")
    if env_path:
        return Path(env_path)

    ui_templates = root_dir / "modules" / "sparky_ui" / "tool" / "templates"
    if ui_templates.exists():
        return ui_templates

    return root_dir / "universe" / "templates"
