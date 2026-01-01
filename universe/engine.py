from __future__ import annotations

from importlib import import_module
import logging
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from universe.admin import (
    admin_link_enabled,
    admin_path,
    DisabledModulesMiddleware,
    build_mount_map,
    fetch_metrics,
    get_module_overrides,
    last_db_check,
    module_enabled,
    overrides_source,
    require_admin,
    set_module_override,
    test_db_health,
)
from universe.ads import ads_enabled, ads_txt_content
from universe.lint import lint_module
from universe.registry import load_modules
from universe.seo import (
    seo_collection_json_ld,
    seo_enabled,
    seo_module_json_ld,
    seo_site_json_ld,
    sitemap_xml,
)
from universe.telemetry import attach_telemetry

logger = logging.getLogger(__name__)

CATEGORY_DESCRIPTIONS = {
    "QR": "Create, verify, and edit QR codes for print and sharing.",
    "Conversion": "Unit conversions across length, mass, volume, and temperature.",
    "Numbers": "Clean and normalize numbers for downstream use.",
    "Money": "Format amounts and currencies into readable output.",
    "Finance": "Quick VAT and percentage calculations for price checks.",
    "Data": "Batch-friendly utilities like CSV normalization.",
    "Marketing QA": "SEO and campaign checks for marketing teams.",
    "Content QA": "Tone, readability, and copy consistency checks.",
    "Text/String": "Text utilities for cleaning, parsing, and transforming strings.",
    "Utilities": "Small, practical tools for quick one-off tasks.",
    "Other": "Useful modules that do not fit a core category.",
}
DEFAULT_CATEGORY_DESCRIPTION = "Practical utilities for quick tasks."


def _slugify(value: str) -> str:
    return value.strip().lower().replace(" ", "-").replace("/", "-")


def build_categories() -> list[dict[str, Any]]:
    overrides = get_module_overrides()
    modules = []
    for module in load_modules().values():
        if not module.get("public", True):
            continue
        name = module.get("name")
        if name and not module_enabled(name, overrides):
            continue
        modules.append(module)
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
    attach_telemetry(app)
    app.add_middleware(DisabledModulesMiddleware, mount_map=build_mount_map())
    admin_prefix = admin_path()

    brand_dir = Path(__file__).parent.parent / "brand"
    if brand_dir.exists():
        app.mount("/brand", StaticFiles(directory=str(brand_dir)), name="brand")

    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    templates.env.auto_reload = True
    templates.env.cache = {}
    templates.env.globals.setdefault("seo_enabled", seo_enabled)
    templates.env.globals.setdefault("seo_site_json_ld", seo_site_json_ld)
    templates.env.globals.setdefault("seo_collection_json_ld", seo_collection_json_ld)
    templates.env.globals.setdefault("seo_module_json_ld", seo_module_json_ld)

    @app.get("/", response_class=HTMLResponse)
    def universe_index(request: Request):
        categories = build_categories()
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "categories": categories,
                "base_path": base_path,
                "adsense_enabled": ads_enabled(),
                "admin_link_enabled": admin_link_enabled(),
                "admin_path": admin_prefix,
            },
        )

    @app.get("/ads.txt", response_class=PlainTextResponse)
    def ads_txt():
        content = ads_txt_content(Path(__file__).parent.parent)
        if not content:
            raise HTTPException(status_code=404, detail="ads.txt not configured")
        return PlainTextResponse(content)

    @app.get("/sitemap.xml", response_class=Response)
    def sitemap(request: Request):
        if not seo_enabled():
            raise HTTPException(status_code=404, detail="SEO disabled")
        base_url = str(request.base_url).rstrip("/")
        categories = build_categories()
        urls = [f"{base_url}/"]
        for category in categories:
            urls.append(f"{base_url}/category/{category['slug']}")
            for module in category.get("modules", []):
                mount = module.get("mount") or f"/{module.get('slug', module['name'])}"
                if not mount.startswith("/"):
                    mount = "/" + mount
                urls.append(f"{base_url}{mount}")
        xml = sitemap_xml(urls)
        return Response(content=xml, media_type="application/xml")

    @app.get("/category/{slug}", response_class=HTMLResponse)
    def category_index(request: Request, slug: str):
        categories = build_categories()
        category = next((item for item in categories if item["slug"] == slug), None)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "category.html",
            {
                "request": request,
                "category": category,
                "base_path": base_path,
                "adsense_enabled": ads_enabled(),
            },
        )

    @app.get(f"{admin_prefix}", response_class=HTMLResponse)
    def admin_index(request: Request, _: None = Depends(require_admin)):
        modules = load_modules()
        overrides = get_module_overrides()
        db_check = last_db_check()
        items: list[dict[str, Any]] = []
        for meta in modules.values():
            name = meta.get("name", "")
            public = bool(meta.get("public", True))
            enabled = module_enabled(name, overrides) if name else True
            lint = lint_module(meta)
            entrypoint = lint.get("entrypoint") or ""
            status = "ok"
            if not enabled:
                status = "disabled"
            elif not lint.get("ok", True):
                status = "error"
            items.append(
                {
                    "name": name,
                    "title": meta.get("title") or name,
                    "category": meta.get("category") or "Other",
                    "mount": meta.get("mount") or f"/{meta.get('slug', name)}",
                    "public": public,
                    "enabled": enabled,
                    "status": status,
                    "source": meta.get("source", ""),
                    "entrypoint": entrypoint,
                    "entrypoint_ok": lint.get("entrypoint_ok", True),
                    "entrypoint_error": lint.get("entrypoint_error", ""),
                    "has_app": lint.get("has_app", False),
                    "has_template": lint.get("has_template", False),
                    "has_core": lint.get("has_core", False),
                    "lint_issues": lint.get("issues", []),
                }
            )

        items.sort(key=lambda item: (item["category"], item["title"]))
        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "modules": items,
                "overrides_source": overrides_source(),
                "db_check": db_check,
                "admin_base": admin_prefix,
            },
        )

    @app.get(f"{admin_prefix}/metrics", response_class=HTMLResponse)
    def admin_metrics(request: Request, _: None = Depends(require_admin)):
        metrics = fetch_metrics()
        return templates.TemplateResponse(
            "admin_metrics.html",
            {"request": request, "metrics": metrics, "admin_base": admin_prefix},
        )

    @app.post(f"{admin_prefix}/toggle")
    def admin_toggle(
        name: str = Form(...),
        enabled: str = Form(...),
        _: None = Depends(require_admin),
    ):
        enable_value = enabled.strip().lower() in {"1", "true", "yes", "on"}
        set_module_override(name, enable_value)
        return RedirectResponse(url=admin_prefix, status_code=303)

    @app.post(f"{admin_prefix}/test-db")
    def admin_test_db(_: None = Depends(require_admin)):
        test_db_health()
        return RedirectResponse(url=admin_prefix, status_code=303)

    modules = load_modules()
    for meta in modules.values():
        if not meta.get("public", True):
            continue
        entrypoints = meta.get("entrypoints") or {}
        api_entry = entrypoints.get("api")
        if not api_entry:
            continue

        try:
            subapp = import_attr(api_entry)
        except Exception:
            logger.exception(
                "Failed to import entrypoint for module %s (%s)",
                meta.get("name", "<unknown>"),
                api_entry,
            )
            continue

        mount_path = meta.get("mount") or f"/{meta.get('slug', meta['name'])}"
        app.mount(mount_path, subapp)

    return app
