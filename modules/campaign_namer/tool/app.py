from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.campaign_namer.core.validate import validate_campaign_name
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="Campaign Naming Validator")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"
SHARED_TEMPLATES = shared_templates_dir(ROOT_DIR)

templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
templates.env.auto_reload = True
templates.env.cache = {}
attach_ads_globals(templates)

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

FLOW_BASE_URL = os.getenv("SPARKY_FLOW_BASE_URL")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    flow_links = resolve_flow_links("campaign_namer", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


def _parse_length(value: str | None, label: str) -> tuple[int | None, str | None]:
    if value is None or value == "":
        return None, None
    try:
        length = int(value)
    except ValueError:
        return None, f"{label} must be a whole number."
    if length < 0:
        return None, f"{label} must be zero or greater."
    return length, None


@app.post("/validate")
def validate(
    name: str | None = Form(None),
    pattern: str | None = Form(None),
    min_length: str | None = Form(None),
    max_length: str | None = Form(None),
    required_tokens: str | None = Form(None),
):
    min_len, error = _parse_length(min_length, "Min length")
    if error:
        return JSONResponse({"error": error}, status_code=400)
    max_len, error = _parse_length(max_length, "Max length")
    if error:
        return JSONResponse({"error": error}, status_code=400)

    result, error = validate_campaign_name(
        name,
        pattern=pattern,
        min_length=min_len,
        max_length=max_len,
        required_tokens=required_tokens,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
