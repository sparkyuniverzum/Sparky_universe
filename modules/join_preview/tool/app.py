from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.join_preview.core.join import preview_join
from universe.flows import resolve_flow_links
from universe.settings import configure_templates, shared_templates_dir
from universe.ads import attach_ads_globals

app = FastAPI(title="Join Preview")

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
    flow_links = resolve_flow_links("join_preview", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/preview")
def preview(
    left_csv: str | None = Form(None),
    right_csv: str | None = Form(None),
    left_key: str | None = Form(None),
    right_key: str | None = Form(None),
    left_header: bool = Form(False),
    right_header: bool = Form(False),
):
    if left_csv is None or right_csv is None:
        return JSONResponse({"error": "Both CSV inputs are required."}, status_code=400)
    if left_key is None or right_key is None:
        return JSONResponse({"error": "Both join keys are required."}, status_code=400)
    result, error = preview_join(
        left_csv,
        right_csv,
        left_key=left_key,
        right_key=right_key,
        left_header=left_header,
        right_header=right_header,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
