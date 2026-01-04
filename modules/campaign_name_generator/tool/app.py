from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.campaign_name_generator.core.generate import generate_campaign_names
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="Campaign Name Generator")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"
SHARED_TEMPLATES = shared_templates_dir(ROOT_DIR)

templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
configure_templates(templates)
attach_ads_globals(templates)

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

FLOW_BASE_URL = os.getenv("SPARKY_FLOW_BASE_URL")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    flow_links = resolve_flow_links("campaign_name_generator", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/generate")
def generate(
    brand: str = Form("brand"),
    channels: str = Form("paid-social,search"),
    offers: str = Form("launch"),
    regions: str = Form("global"),
    objective: str = Form("acq"),
    date: str | None = Form(None),
    separator: str = Form("_"),
    limit: int = Form(200),
):
    payload, error = generate_campaign_names(
        brand=brand,
        channels=channels,
        offers=offers,
        regions=regions,
        objective=objective,
        date=date,
        separator=separator or "_",
        limit=limit,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
