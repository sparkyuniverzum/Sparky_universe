from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def shared_templates_dir(root_dir: Path) -> Path:
    env_path = os.getenv("SPARKY_SHARED_TEMPLATES")
    if env_path:
        return Path(env_path)

    ui_templates = root_dir / "modules" / "sparky_ui" / "tool" / "templates"
    if ui_templates.exists():
        return ui_templates

    return root_dir / "universe" / "templates"


def _flag(name: str, default: str = "off") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def templates_auto_reload() -> bool:
    return _flag("SPARKY_TEMPLATE_RELOAD", "off")


def configure_templates(templates: Any) -> None:
    auto_reload = templates_auto_reload()
    templates.env.auto_reload = auto_reload
    if auto_reload:
        templates.env.cache = {}
