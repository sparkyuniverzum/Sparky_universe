from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.aurelia.core.logs import list_events, log_stats, record_event
from universe.admin import require_admin
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="Aurelia")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"
SHARED_TEMPLATES = shared_templates_dir(ROOT_DIR)
SRC_DIR = BASE_DIR.parent / "src"

COOKIE_NAME = "aurelia_user_id"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365
MAX_PAYLOAD_BYTES = 20000
REDACT_KEYS = {
    "text",
    "journalentry",
    "journal_entry",
    "entry",
    "raw",
}


templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
configure_templates(templates)

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")
if SRC_DIR.exists():
    app.mount("/src", StaticFiles(directory=SRC_DIR), name="aurelia-src")


def _get_or_create_user_id(request: Request) -> tuple[str, bool]:
    existing = request.cookies.get(COOKIE_NAME)
    if existing:
        return existing, False
    return str(uuid.uuid4()), True


def _sanitize_payload(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return None
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            if key_str.lower() in REDACT_KEYS:
                continue
            out[key_str] = _sanitize_payload(item, depth + 1)
        return out
    if isinstance(value, list):
        return [_sanitize_payload(item, depth + 1) for item in value[:40]]
    if isinstance(value, str):
        return value[:200]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:200]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    user_id, is_new = _get_or_create_user_id(request)
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "base_path": base_path,
            "user_id": user_id,
            "planet_seed": None,
        },
    )
    if is_new:
        response.set_cookie(
            COOKIE_NAME,
            user_id,
            max_age=COOKIE_MAX_AGE,
            samesite="Lax",
        )
    return response


@app.post("/api/log")
async def log_event(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    if not isinstance(payload, dict):
        return JSONResponse({"error": "Invalid payload"}, status_code=400)

    user_id = payload.get("user_id") or payload.get("userId")
    if not user_id:
        user_id = request.cookies.get(COOKIE_NAME)

    event_type = payload.get("event_type") or payload.get("eventType") or "sync"
    event_type = str(event_type).strip().lower() or "sync"

    stripped = {
        key: value
        for key, value in payload.items()
        if key not in {"user_id", "userId", "event_type", "eventType"}
    }
    sanitized = _sanitize_payload(stripped)

    try:
        size = len(json.dumps(sanitized, ensure_ascii=True))
    except Exception:
        size = MAX_PAYLOAD_BYTES + 1

    if size > MAX_PAYLOAD_BYTES:
        return JSONResponse({"error": "Payload too large"}, status_code=400)

    event_id = record_event(user_id, event_type, sanitized)
    return JSONResponse({"ok": True, "id": event_id})


@app.get("/admin/logs", response_class=HTMLResponse)
def admin_logs(
    request: Request,
    limit: int = 100,
    user_hash: str | None = None,
    event_type: str | None = None,
    _: None = Depends(require_admin),
):
    base_path = request.url.path.split("/admin", 1)[0]
    stats = log_stats()
    last_event_at = stats.get("last_event_at")
    if hasattr(last_event_at, "isoformat"):
        stats["last_event_at"] = last_event_at.isoformat()
    elif isinstance(last_event_at, (int, float)):
        stats["last_event_at"] = datetime.fromtimestamp(
            last_event_at, tz=timezone.utc
        ).isoformat()
    logs = list_events(limit=limit, user_hash=user_hash, event_type=event_type)
    entries = []
    for log in logs:
        created_at = log.get("created_at")
        if hasattr(created_at, "isoformat"):
            created_at = created_at.isoformat()
        entries.append(
            {
                "id": log.get("id"),
                "user_hash": log.get("user_hash"),
                "event_type": log.get("event_type"),
                "created_at": created_at,
                "payload_json": json.dumps(log.get("payload") or {}, ensure_ascii=True),
            }
        )
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "base_path": base_path,
            "stats": stats,
            "logs": entries,
            "limit": limit,
            "user_hash": user_hash or "",
            "event_type": event_type or "",
        },
    )
