from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.creative_spec_check.core.check import check_specs
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="Creative Spec Check")

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
    flow_links = resolve_flow_links("creative_spec_check", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


def _parse_int(value: str | None, label: str) -> tuple[int | None, str | None]:
    if value is None or value == "":
        return None, None
    try:
        number = int(value)
    except ValueError:
        return None, f"{label} must be a whole number."
    return number, None


@app.post("/check")
def check(
    width: str | None = Form(None),
    height: str | None = Form(None),
    platform: str | None = Form(None),
):
    width_value, error = _parse_int(width, "Width")
    if error:
        return JSONResponse({"error": error}, status_code=400)
    height_value, error = _parse_int(height, "Height")
    if error:
        return JSONResponse({"error": error}, status_code=400)

    result, error = check_specs(width=width_value, height=height_value, platform=platform)
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
