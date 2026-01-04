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
from universe.satellite_bavaria_holiday_orbit import (
    ensure_latest_snapshot as ensure_bavaria_snapshot,
    fetch_latest_snapshot as fetch_bavaria_snapshot,
)
from universe.holiday_digest import (
    active_subscription_for_email as holiday_subscription_for_email,
    apply_stripe_event as holiday_apply_stripe_event,
    create_checkout_session as holiday_create_checkout_session,
    db_available as holiday_db_available,
    holiday_digest_enabled,
    holiday_price_label,
    remove_subscription as holiday_remove_subscription,
    smtp_configured as holiday_smtp_configured,
    stripe_configured as holiday_stripe_configured,
)
from universe.monitoring import (
    apply_stripe_event,
    active_subscription_for_email,
    create_checkout_session,
    create_free_watcher,
    create_paid_watcher,
    crypto_metrics,
    finance_metrics,
    metric_allowed,
    monitor_price_label,
    monitoring_enabled,
    parse_threshold,
    public_base_url,
    remove_watcher,
    smtp_configured,
    stripe_configured,
    verify_stripe_event,
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
COMPARATOR_LABELS = {
    "gt": "Above",
    "lt": "Below",
    "change_abs": "Change (absolute)",
    "change_pct": "Change (%)",
}

WATCH_NOTICE = {
    "ok": ("success", "Monitoring is active. You will receive updates by email."),
    "paid": ("success", "Payment confirmed. Monitoring will activate shortly."),
    "error": ("error", "We could not create this monitor."),
}

WATCH_ERROR_MESSAGES = {
    "duplicate": "This monitor already exists.",
    "invalid_email": "Enter a valid email address.",
    "invalid_metric": "Select a valid metric.",
    "invalid_threshold": "Enter a numeric threshold.",
    "invalid_request": "Request is invalid.",
    "limit_reached": "Limit reached for this plan.",
    "email_not_configured": "Email delivery is not configured yet.",
    "stripe_not_configured": "Billing is not configured yet.",
    "stripe_missing": "Billing provider is not available.",
    "db_unavailable": "Database is not available.",
}

HOLIDAY_NOTICE = {
    "ok": ("success", "Subscription active. You will receive monthly holiday alerts."),
    "paid": ("success", "Payment confirmed. Alerts will start next month."),
    "error": ("error", "We could not start the subscription."),
    "active": ("info", "You already have an active subscription."),
}

HOLIDAY_ERROR_MESSAGES = {
    "invalid_email": "Enter a valid email address.",
    "email_not_configured": "Email delivery is not configured yet.",
    "stripe_not_configured": "Billing is not configured yet.",
    "stripe_missing": "Billing provider is not available.",
    "db_unavailable": "Database is not available.",
    "cancelled": "Payment was cancelled.",
}


def _slugify(value: str) -> str:
    return value.strip().lower().replace(" ", "-").replace("/", "-")


def _parse_story_entry(raw: str) -> dict[str, Any]:
    lines = [line.rstrip() for line in raw.splitlines()]
    content_lines = [line for line in lines if line.strip()]
    title = content_lines[0] if content_lines else "Story"
    subtitle = content_lines[1] if len(content_lines) > 1 else ""
    body_lines = lines[lines.index(content_lines[1]) + 1 :] if len(content_lines) > 1 else lines
    paragraphs: list[list[str]] = []
    current: list[str] = []
    for line in body_lines:
        if not line.strip():
            if current:
                paragraphs.append(current)
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(current)
    return {"title": title, "subtitle": subtitle, "paragraphs": paragraphs}


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


def _watch_notice(request: Request) -> dict[str, str] | None:
    status = request.query_params.get("watch", "").strip().lower()
    reason = request.query_params.get("reason", "").strip().lower()
    if not status:
        return None
    level, message = WATCH_NOTICE.get(status, ("info", ""))
    if status == "error":
        message = WATCH_ERROR_MESSAGES.get(reason, message)
    if not message:
        return None
    return {"level": level, "message": message}


def _holiday_notice(request: Request) -> dict[str, str] | None:
    status = request.query_params.get("subscribe", "").strip().lower()
    reason = request.query_params.get("reason", "").strip().lower()
    if not status:
        return None
    level, message = HOLIDAY_NOTICE.get(status, ("info", ""))
    if status == "error":
        message = HOLIDAY_ERROR_MESSAGES.get(reason, message)
    if not message:
        return None
    return {"level": level, "message": message}


def _sanitize_return_path(value: str) -> str:
    if not value:
        return "/"
    if not value.startswith("/"):
        return "/" + value
    return value


def _watch_redirect(return_path: str, status: str, reason: str | None = None) -> RedirectResponse:
    safe_path = _sanitize_return_path(return_path)
    params = {"watch": status}
    if reason:
        params["reason"] = reason
    query = "&".join(f"{key}={value}" for key, value in params.items())
    url = f"{safe_path}?{query}"
    return RedirectResponse(url=url, status_code=303)


def _holiday_redirect(return_path: str, status: str, reason: str | None = None) -> RedirectResponse:
    safe_path = _sanitize_return_path(return_path)
    params = {"subscribe": status}
    if reason:
        params["reason"] = reason
    query = "&".join(f"{key}={value}" for key, value in params.items())
    url = f"{safe_path}?{query}"
    return RedirectResponse(url=url, status_code=303)


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
                "story_path": f"{base_path}/story/axiom",
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
        urls.append(f"{base_url}/story/axiom")
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
            {
                "request": request,
                "metrics": metrics,
                "admin_base": admin_prefix,
                "group_links": [
                    {"label": "Stars", "href": f"{admin_prefix}/metrics/stars"},
                    {"label": "Planets", "href": f"{admin_prefix}/metrics/planets"},
                    {"label": "Satellites", "href": f"{admin_prefix}/metrics/satellites"},
                ],
            },
        )

    def _group_metrics(metrics: dict[str, Any], names: set[str]) -> dict[str, Any]:
        if not metrics.get("ok"):
            return {
                "ok": False,
                "detail": metrics.get("detail", ""),
                "summary": {},
                "by_module_usage": [],
                "by_module": [],
            }
        by_module_usage = [
            row for row in metrics.get("by_module_usage", []) if row.get("module") in names
        ]
        by_module = [
            (name, count)
            for name, count in metrics.get("by_module", [])
            if name in names
        ]
        total_views = sum(row.get("page_views", 0) for row in by_module_usage)
        total_actions = sum(row.get("actions", 0) for row in by_module_usage)
        total_sessions = sum(row.get("sessions", 0) for row in by_module_usage)
        conversion = round((total_actions / total_views) * 100, 1) if total_views else 0.0
        return {
            "ok": True,
            "detail": metrics.get("detail", ""),
            "summary": {
                "item_count": len(by_module_usage),
                "page_views_7d": total_views,
                "actions_7d": total_actions,
                "sessions_7d": total_sessions,
                "conversion_rate_7d": conversion,
            },
            "by_module_usage": by_module_usage,
            "by_module": by_module,
        }

    def _planet_names() -> set[str]:
        return {
            meta.get("name", "")
            for meta in load_modules().values()
            if meta.get("category") == "Planets"
        }

    def _star_names() -> set[str]:
        return {
            meta.get("name", "")
            for meta in load_modules().values()
            if meta.get("category") != "Planets"
        }

    def _satellite_names() -> set[str]:
        names = set()
        for satellite in list_satellites():
            slug = satellite.get("slug") or satellite.get("id") or ""
            if slug:
                names.add(f"satellite:{slug}")
        return names

    def _group_links() -> list[dict[str, str]]:
        return [
            {"label": "All metrics", "href": f"{admin_prefix}/metrics"},
            {"label": "Stars", "href": f"{admin_prefix}/metrics/stars"},
            {"label": "Planets", "href": f"{admin_prefix}/metrics/planets"},
            {"label": "Satellites", "href": f"{admin_prefix}/metrics/satellites"},
        ]

    @app.get(f"{admin_prefix}/metrics/stars", response_class=HTMLResponse)
    def admin_metrics_stars(request: Request, _: None = Depends(require_admin)):
        metrics = fetch_metrics()
        group_metrics = _group_metrics(metrics, _star_names())
        return templates.TemplateResponse(
            "admin_metrics_group.html",
            {
                "request": request,
                "metrics": group_metrics,
                "group_name": "Stars",
                "admin_base": admin_prefix,
                "group_links": _group_links(),
            },
        )

    @app.get(f"{admin_prefix}/metrics/planets", response_class=HTMLResponse)
    def admin_metrics_planets(request: Request, _: None = Depends(require_admin)):
        metrics = fetch_metrics()
        group_metrics = _group_metrics(metrics, _planet_names())
        return templates.TemplateResponse(
            "admin_metrics_group.html",
            {
                "request": request,
                "metrics": group_metrics,
                "group_name": "Planets",
                "admin_base": admin_prefix,
                "group_links": _group_links(),
            },
        )

    @app.get(f"{admin_prefix}/metrics/satellites", response_class=HTMLResponse)
    def admin_metrics_satellites(request: Request, _: None = Depends(require_admin)):
        metrics = fetch_metrics()
        group_metrics = _group_metrics(metrics, _satellite_names())
        return templates.TemplateResponse(
            "admin_metrics_group.html",
            {
                "request": request,
                "metrics": group_metrics,
                "group_name": "Satellites",
                "admin_base": admin_prefix,
                "group_links": _group_links(),
            },
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
        watch_notice = _watch_notice(request)
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
                "monitoring_enabled": monitoring_enabled(),
                "monitor_metrics": finance_metrics(snapshot),
                "monitor_price_label": monitor_price_label(),
                "monitor_action": f"{base_path}/monitoring/watch",
                "return_path": request.url.path,
                "comparator_labels": COMPARATOR_LABELS,
                "watch_notice": watch_notice,
                "monitor_ready": smtp_configured(),
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
        watch_notice = _watch_notice(request)
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
                "monitoring_enabled": monitoring_enabled(),
                "monitor_metrics": crypto_metrics(snapshot),
                "monitor_price_label": monitor_price_label(),
                "monitor_action": f"{base_path}/monitoring/watch",
                "return_path": request.url.path,
                "comparator_labels": COMPARATOR_LABELS,
                "watch_notice": watch_notice,
                "monitor_ready": smtp_configured(),
            },
        )

    @app.get("/satellites/crypto-orbit/latest")
    def crypto_orbit_latest():
        snapshot, snapshot_error = ensure_crypto_snapshot()
        if snapshot_error and not snapshot:
            raise HTTPException(status_code=503, detail=snapshot_error)
        return JSONResponse(snapshot or {})

    @app.get("/story/axiom", response_class=HTMLResponse)
    def story_axiom(request: Request):
        story_path = Path(__file__).parent.parent / "brand" / "Story" / "entries" / "ENTRY_001_AXIOM.md"
        try:
            raw = story_path.read_text(encoding="utf-8")
        except Exception as exc:
            raise HTTPException(status_code=404, detail="Story not available") from exc
        entry = _parse_story_entry(raw)
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "story_axiom.html",
            {
                "request": request,
                "entry": entry,
                "home_path": f"{base_path}/",
            },
        )

    @app.get("/satellites/bavaria-holiday-orbit", response_class=HTMLResponse)
    def bavaria_holiday_orbit_public(request: Request):
        snapshot, snapshot_error = ensure_bavaria_snapshot()
        data_entries = snapshot.get("data", []) if snapshot else []
        snapshot_json = (
            json.dumps(snapshot, indent=2, ensure_ascii=True) if snapshot else ""
        )
        base_path = request.scope.get("root_path", "").rstrip("/")
        subscribe_notice = _holiday_notice(request)
        return templates.TemplateResponse(
            "satellite_bavaria_holiday_orbit.html",
            {
                "request": request,
                "snapshot": snapshot,
                "snapshot_error": snapshot_error,
                "snapshot_json": snapshot_json,
                "data_entries": data_entries,
                "api_path": f"{base_path}/satellites/bavaria-holiday-orbit/latest",
                "home_path": f"{base_path}/",
                "subscribe_action": f"{base_path}/satellites/bavaria-holiday-orbit/subscribe",
                "return_path": request.url.path,
                "subscribe_notice": subscribe_notice,
                "holiday_digest_enabled": holiday_digest_enabled(),
                "holiday_price_label": holiday_price_label(),
                "holiday_ready": holiday_smtp_configured(),
            },
        )

    @app.get("/satellites/bavaria-holiday-orbit/latest")
    def bavaria_holiday_orbit_latest():
        snapshot, _, snapshot_error = fetch_bavaria_snapshot()
        if snapshot_error and not snapshot:
            raise HTTPException(status_code=503, detail=snapshot_error)
        return JSONResponse(snapshot or {})

    @app.post("/satellites/bavaria-holiday-orbit/subscribe")
    def bavaria_holiday_subscribe(
        request: Request,
        email: str = Form(...),
        return_path: str = Form("/"),
    ):
        if not holiday_digest_enabled():
            raise HTTPException(status_code=404, detail="Subscriptions disabled")
        if not holiday_db_available():
            return _holiday_redirect(return_path, "error", "db_unavailable")
        if not holiday_smtp_configured():
            return _holiday_redirect(return_path, "error", "email_not_configured")
        if not email or "@" not in email:
            return _holiday_redirect(return_path, "error", "invalid_email")

        existing = holiday_subscription_for_email(email)
        if existing:
            return _holiday_redirect(return_path, "active")

        if not holiday_stripe_configured():
            return _holiday_redirect(return_path, "error", "stripe_not_configured")

        base_url = public_base_url(str(request.base_url))
        success_url = f"{base_url}/satellites/bavaria-holiday-orbit/thanks"
        cancel_url = (
            f"{base_url}{_sanitize_return_path(return_path)}"
            "?subscribe=error&reason=cancelled"
        )
        checkout_url, error = holiday_create_checkout_session(
            email=email.strip(),
            success_url=success_url,
            cancel_url=cancel_url,
        )
        if error or not checkout_url:
            return _holiday_redirect(return_path, "error", error or "stripe_not_configured")
        return RedirectResponse(url=checkout_url, status_code=303)

    @app.get("/satellites/bavaria-holiday-orbit/thanks", response_class=HTMLResponse)
    def bavaria_holiday_thanks(request: Request):
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "holiday_digest_thanks.html",
            {
                "request": request,
                "home_path": f"{base_path}/",
            },
        )

    @app.get(
        "/satellites/bavaria-holiday-orbit/unsubscribe",
        response_class=PlainTextResponse,
    )
    def bavaria_holiday_unsubscribe(id: str, sig: str):
        ok = holiday_remove_subscription(id, sig)
        if not ok:
            raise HTTPException(status_code=403, detail="Invalid unsubscribe link")
        return PlainTextResponse("You have been unsubscribed.")

    @app.post("/satellites/crypto-orbit/refresh")
    def crypto_orbit_refresh(request: Request):
        token = request.headers.get("x-satellite-token", "")
        if not crypto_token_valid(token):
            raise HTTPException(status_code=403, detail="Forbidden")
        snapshot, error = run_crypto_orbit()
        if error:
            raise HTTPException(status_code=503, detail=error)
        return JSONResponse({"ok": True, "snapshot": snapshot})

    @app.post("/monitoring/watch")
    def monitoring_watch(
        request: Request,
        email: str = Form(...),
        source_key: str = Form(...),
        metric_key: str = Form(...),
        comparator: str = Form(...),
        threshold: str = Form(...),
        frequency: str = Form(...),
        return_path: str = Form("/"),
    ):
        if not monitoring_enabled():
            raise HTTPException(status_code=404, detail="Monitoring disabled")

        normalized_comparator = comparator.strip().lower()
        normalized_frequency = frequency.strip().lower()
        if normalized_comparator not in COMPARATOR_LABELS:
            return _watch_redirect(return_path, "error", "invalid_request")
        if normalized_frequency not in {"daily", "hourly"}:
            return _watch_redirect(return_path, "error", "invalid_request")

        threshold_value = parse_threshold(threshold)
        if threshold_value is None:
            return _watch_redirect(return_path, "error", "invalid_threshold")
        if not metric_allowed(source_key.strip(), metric_key.strip()):
            return _watch_redirect(return_path, "error", "invalid_metric")
        if not smtp_configured():
            return _watch_redirect(return_path, "error", "email_not_configured")

        if normalized_frequency == "hourly":
            active_subscription = active_subscription_for_email(email.strip())
            if active_subscription:
                watcher_id, error = create_paid_watcher(
                    email=email.strip(),
                    source_key=source_key.strip(),
                    metric_key=metric_key.strip(),
                    comparator=normalized_comparator,
                    threshold=threshold_value,
                    frequency=normalized_frequency,
                    subscription_id=active_subscription,
                    customer_id=None,
                )
                if error:
                    return _watch_redirect(return_path, "error", error)
                return _watch_redirect(return_path, "ok")
            if not stripe_configured():
                return _watch_redirect(return_path, "error", "stripe_not_configured")
            base_url = public_base_url(str(request.base_url))
            success_url = f"{base_url}/monitoring/thanks"
            cancel_url = (
                f"{base_url}{_sanitize_return_path(return_path)}"
                "?watch=error&reason=invalid_request"
            )
            checkout_url, error = create_checkout_session(
                email=email.strip(),
                source_key=source_key.strip(),
                metric_key=metric_key.strip(),
                comparator=normalized_comparator,
                threshold=threshold_value,
                frequency=normalized_frequency,
                success_url=success_url,
                cancel_url=cancel_url,
            )
            if error or not checkout_url:
                return _watch_redirect(return_path, "error", error or "invalid_request")
            return RedirectResponse(url=checkout_url, status_code=303)

        watcher_id, error = create_free_watcher(
            email=email.strip(),
            source_key=source_key.strip(),
            metric_key=metric_key.strip(),
            comparator=normalized_comparator,
            threshold=threshold_value,
            frequency=normalized_frequency,
        )
        if error:
            return _watch_redirect(return_path, "error", error)
        return _watch_redirect(return_path, "ok")

    @app.get("/monitoring/thanks", response_class=HTMLResponse)
    def monitoring_thanks(request: Request):
        base_path = request.scope.get("root_path", "").rstrip("/")
        return templates.TemplateResponse(
            "monitoring_thanks.html",
            {
                "request": request,
                "home_path": f"{base_path}/",
            },
        )

    @app.get("/monitoring/unsubscribe", response_class=PlainTextResponse)
    def monitoring_unsubscribe(id: str, sig: str):
        ok = remove_watcher(id, sig)
        if not ok:
            raise HTTPException(status_code=403, detail="Invalid unsubscribe link")
        return PlainTextResponse("You have been unsubscribed.")

    @app.post("/stripe/webhook")
    async def stripe_webhook(request: Request):
        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")
        event, error = verify_stripe_event(payload, signature)
        if error or not event:
            raise HTTPException(status_code=400, detail="Invalid webhook")
        apply_stripe_event(event)
        holiday_apply_stripe_event(event)
        return JSONResponse({"ok": True})

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
