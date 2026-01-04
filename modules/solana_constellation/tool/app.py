from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.solana_constellation.core.config import load_config
from modules.solana_constellation.core.ingest import refresh_from_rpc
from modules.solana_constellation.core.rpc import SolanaRpcError
from modules.solana_constellation.core.storage import (
    event_count,
    last_ingest_at,
    list_events,
    list_recent_events,
    raw_count,
)
from modules.solana_constellation.core.stars import (
    STAR_DEFS,
    STAR_ORDER,
    build_risk_snapshot,
    build_star_snapshot,
    recent_window,
)
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="Solana Constellation")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"
SHARED_TEMPLATES = shared_templates_dir(ROOT_DIR)

templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
configure_templates(templates)

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")


def _constellation_snapshot() -> dict:
    stars = []
    for star_id in STAR_ORDER:
        if star_id == "risk":
            continue
        history = list_events(star_id, limit=25)
        recent = list_recent_events(star_id, since=recent_window(24 * 7))
        stars.append(
            build_star_snapshot(
                star_id,
                history,
                recent_events=recent,
            )
        )
    risk = build_risk_snapshot(stars)
    stars.append(risk)
    return {
        "constellation": "solana",
        "stars": stars,
        "meta": {
            "raw_events": raw_count(),
            "canonical_events": event_count(),
            "last_ingest_at": last_ingest_at(),
        },
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "base_path": base_path,
            "star_defs": [STAR_DEFS[key] | {"id": key} for key in STAR_ORDER],
        },
    )


@app.get("/api/stars")
def api_stars():
    return JSONResponse(_constellation_snapshot())


@app.post("/api/refresh")
def api_refresh(request: Request):
    config = load_config()
    token = request.headers.get("x-constellation-token", "").strip()
    if config.refresh_token and token != config.refresh_token:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        result = refresh_from_rpc()
    except SolanaRpcError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not result.get("ok", True):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)
