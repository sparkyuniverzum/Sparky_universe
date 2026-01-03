from __future__ import annotations

from importlib import import_module
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)
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
from universe.errors import ValidationNormalizeMiddleware
from universe.lint import lint_module
from universe.limits import (
    RequestLimitsMiddleware,
    max_body_bytes,
    module_max_body_overrides,
    module_timeout_overrides,
    request_timeout_seconds,
)
from universe.registry import load_modules
from universe.seo import (
    seo_collection_json_ld,
    seo_enabled,
    seo_module_json_ld,
    seo_site_json_ld,
    sitemap_xml,
)
from universe.satellite_finance_orbit import fetch_latest_snapshot
from universe.satellite_crypto_orbit import (
    ensure_latest_snapshot as ensure_crypto_snapshot,
    refresh_token_valid as crypto_token_valid,
    run_crypto_orbit,
)
from universe.satellites import list_satellites
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
    "Learning Shortcuts": "Fast learning aids for studying, recall, and practice.",
    "Text/String": "Text utilities for cleaning, parsing, and transforming strings.",
    "Utilities": "Small, practical tools for quick one-off tasks.",
    "Planets": "Larger tools for full situations, not single steps.",
    "Other": "Useful modules that do not fit a core category.",
}
DEFAULT_CATEGORY_DESCRIPTION = "Practical utilities for quick tasks."
CATEGORY_ORDER = ["Planets"]


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
    def _category_sort(entry: tuple[str, list[dict[str, Any]]]) -> tuple[int, str]:
        name = entry[0]
        if name in CATEGORY_ORDER:
            return (0, CATEGORY_ORDER.index(name))
        return (1, name.lower())

    for category, items in sorted(grouped.items(), key=_category_sort):
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
    mount_map = build_mount_map()
    admin_prefix = admin_path()
    app.add_middleware(ValidationNormalizeMiddleware)
    app.add_middleware(DisabledModulesMiddleware, mount_map=mount_map)
    app.add_middleware(
        RequestLimitsMiddleware,
        mount_map=mount_map,
        admin_prefix=admin_prefix,
        max_body=max_body_bytes(),
        timeout_seconds=request_timeout_seconds(),
        module_max_body=module_max_body_overrides(),
        module_timeouts=module_timeout_overrides(),
    )
    attach_telemetry(app)

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
        satellites = list_satellites()
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "categories": categories,
                "satellites": satellites,
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
        satellites = list_satellites()
        urls = [f"{base_url}/"]
        if satellites:
            urls.append(f"{base_url}/satellites")
        for satellite in satellites:
            mount = satellite.get("mount", "")
            if mount:
                urls.append(f"{base_url}{mount}")
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

    @app.get("/satellites", response_class=HTMLResponse)
    def satellites_index(request: Request):
        satellites = list_satellites()
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "satellites.html",
            {
                "request": request,
                "satellites": satellites,
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
                "satellites": list_satellites(),
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

    @app.get("/satellites/finance-orbit", response_class=HTMLResponse)
    def finance_orbit_public(request: Request):
        snapshot, snapshot_error = fetch_latest_snapshot()
        data_entries = snapshot.get("data", []) if snapshot else []
        repo_entry = next(
            (item for item in data_entries if item.get("key") == "REPO_RATE"),
            None,
        )
        snapshot_json = (
            json.dumps(snapshot, indent=2, ensure_ascii=True) if snapshot else ""
        )
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "satellite_finance_orbit.html",
            {
                "request": request,
                "snapshot": snapshot,
                "snapshot_error": snapshot_error,
                "snapshot_json": snapshot_json,
                "data_entries": data_entries,
                "repo_entry": repo_entry,
                "api_path": f"{base_path}/satellites/finance-orbit/latest",
                "home_path": f"{base_path}/",
            },
        )

    @app.get("/satellites/finance-orbit/latest")
    def finance_orbit_latest():
        snapshot, snapshot_error = fetch_latest_snapshot()
        if snapshot_error:
            raise HTTPException(status_code=503, detail=snapshot_error)
        return JSONResponse(snapshot or {})

    @app.get("/satellites/crypto-orbit", response_class=HTMLResponse)
    def crypto_orbit_public(request: Request):
        snapshot, snapshot_error = ensure_crypto_snapshot()
        data_entries = snapshot.get("data", []) if snapshot else []
        top_entry = data_entries[0] if data_entries else None
        snapshot_json = (
            json.dumps(snapshot, indent=2, ensure_ascii=True) if snapshot else ""
        )
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "satellite_crypto_orbit.html",
            {
                "request": request,
                "snapshot": snapshot,
                "snapshot_error": snapshot_error,
                "snapshot_json": snapshot_json,
                "data_entries": data_entries,
                "top_entry": top_entry,
                "api_path": f"{base_path}/satellites/crypto-orbit/latest",
                "home_path": f"{base_path}/",
            },
        )

    @app.get("/satellites/crypto-orbit/latest")
    def crypto_orbit_latest():
        snapshot, snapshot_error = ensure_crypto_snapshot()
        if snapshot_error and not snapshot:
            raise HTTPException(status_code=503, detail=snapshot_error)
        return JSONResponse(snapshot or {})

    @app.post("/satellites/crypto-orbit/refresh")
    def crypto_orbit_refresh(request: Request):
        token = request.headers.get("x-satellite-token", "")
        if not crypto_token_valid(token):
            raise HTTPException(status_code=403, detail="Forbidden")
        snapshot, error = run_crypto_orbit()
        if error:
            raise HTTPException(status_code=503, detail=error)
        return JSONResponse({"ok": True, "snapshot": snapshot})

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
