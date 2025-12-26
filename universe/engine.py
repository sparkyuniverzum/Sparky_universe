from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from universe.registry import load_modules


def import_attr(path: str) -> Any:
    if ":" not in path:
        raise ValueError(f"Invalid entrypoint '{path}'. Expected module:attr.")
    module_path, attr = path.split(":", 1)
    module = import_module(module_path)
    return getattr(module, attr)


def build_app() -> FastAPI:
    app = FastAPI(title="Sparky Universe")

    brand_dir = Path(__file__).parent.parent / "brand"
    if brand_dir.exists():
        app.mount("/brand", StaticFiles(directory=str(brand_dir)), name="brand")

    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

    @app.get("/", response_class=HTMLResponse)
    def universe_index(request: Request):
        modules = list(load_modules().values())
        modules.sort(key=lambda item: item.get("title") or item.get("name", ""))
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "modules": modules},
        )

    modules = load_modules()
    for meta in modules.values():
        entrypoints = meta.get("entrypoints") or {}
        api_entry = entrypoints.get("api")
        if not api_entry:
            continue

        try:
            subapp = import_attr(api_entry)
        except Exception:
            continue

        mount_path = meta.get("mount") or f"/{meta.get('slug', meta['name'])}"
        app.mount(mount_path, subapp)

    return app
