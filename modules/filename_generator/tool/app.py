from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.filename_generator.core.generate import generate_filenames
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="Filename Generator")

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
    flow_links = resolve_flow_links("filename_generator", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/generate")
def generate(
    prefix: str | None = Form("file"),
    extension: str | None = Form("txt"),
    count: int = Form(20),
    start: int = Form(1),
    width: int = Form(4),
    date_format: str = Form("YYYYMMDD"),
    separator: str = Form("_"),
):
    payload, error = generate_filenames(
        prefix=prefix,
        extension=extension,
        count=count,
        start=start,
        width=width,
        date_format=date_format,
        separator=separator or "_",
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
