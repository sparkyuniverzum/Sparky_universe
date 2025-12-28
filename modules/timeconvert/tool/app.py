from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.timeconvert.core.convert import convert_time, list_units
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir
from universe.ads import attach_ads_globals

app = FastAPI(title="Time Converter")

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
    flow_links = resolve_flow_links("timeconvert", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "flow_links": flow_links,
            "base_path": base_path,
            "units": list_units(),
        },
    )


@app.post("/convert")
def convert(
    value: str | None = Form(None),
    from_unit: str = Form("s"),
    to_unit: str = Form("min"),
    decimals: int = Form(4),
):
    result, error = convert_time(value, from_unit, to_unit, decimals=decimals)
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
