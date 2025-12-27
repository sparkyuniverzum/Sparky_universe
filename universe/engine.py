from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from universe.registry import load_modules

CATEGORY_DESCRIPTIONS = {
    "QR": "Create, verify, and edit QR codes for print and sharing.",
    "Conversion": "Unit conversions across length, mass, volume, and temperature.",
    "Numbers": "Clean and normalize numbers for downstream use.",
    "Money": "Format amounts and currencies into readable output.",
    "Finance": "Quick VAT and percentage calculations for price checks.",
    "Data": "Batch-friendly utilities like CSV normalization.",
    "Utilities": "Small, practical tools for quick one-off tasks.",
    "Other": "Useful modules that do not fit a core category.",
}
DEFAULT_CATEGORY_DESCRIPTION = "Practical utilities for quick tasks."


def _slugify(value: str) -> str:
    return value.strip().lower().replace(" ", "-")


def build_categories() -> list[dict[str, Any]]:
    modules = [
        module for module in load_modules().values() if module.get("public", True)
    ]
    modules.sort(key=lambda item: item.get("title") or item.get("name", ""))
    grouped: dict[str, list[dict[str, Any]]] = {}
    for module in modules:
        category = module.get("category") or "Other"
        grouped.setdefault(str(category), []).append(module)

    categories: list[dict[str, Any]] = []
    for category, items in sorted(grouped.items(), key=lambda item: item[0].lower()):
        items.sort(key=lambda item: item.get("title") or item.get("name", ""))
        categories.append(
            {
                "name": category,
                "slug": _slugify(category),
                "description": CATEGORY_DESCRIPTIONS.get(
                    category, DEFAULT_CATEGORY_DESCRIPTION
                ),
                "modules": items,
            }
        )
    return categories


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
    templates.env.auto_reload = True
    templates.env.cache = {}

    @app.get("/", response_class=HTMLResponse)
    def universe_index(request: Request):
        categories = build_categories()
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "categories": categories, "base_path": base_path},
        )

    @app.get("/category/{slug}", response_class=HTMLResponse)
    def category_index(request: Request, slug: str):
        categories = build_categories()
        category = next((item for item in categories if item["slug"] == slug), None)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "category.html",
            {"request": request, "category": category, "base_path": base_path},
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
