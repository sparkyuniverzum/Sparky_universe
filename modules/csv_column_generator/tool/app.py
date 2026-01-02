from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.csv_column_generator.core.generate import generate_column
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="CSV Column Generator")

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
    flow_links = resolve_flow_links("csv_column_generator", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/generate")
def generate(
    mode: str = Form("sequence"),
    count: int = Form(50),
    start: int = Form(1),
    step: int = Form(1),
    width: int = Form(0),
    min_value: int = Form(1),
    max_value: int = Form(100),
    choices: str | None = Form(None),
    unique: str | None = Form(None),
    prefix: str | None = Form(None),
    suffix: str | None = Form(None),
):
    payload, error = generate_column(
        mode=mode,
        count=count,
        start=start,
        step=step,
        width=width,
        min_value=min_value,
        max_value=max_value,
        choices=choices,
        unique=bool(unique),
        prefix=prefix,
        suffix=suffix,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
