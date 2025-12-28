from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.csvsamplegen.core.generate import generate_csv_sample
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="CSV Sample Generator")

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
    flow_links = resolve_flow_links("csvsamplegen", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/generate")
def generate(
    columns: str | None = Form(None),
    rows: str | None = Form(None),
    seed: str | None = Form(None),
):
    result, error = generate_csv_sample(columns, rows, seed=seed)
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result


@app.post("/download")
def download(
    columns: str | None = Form(None),
    rows: str | None = Form(None),
    seed: str | None = Form(None),
):
    result, error = generate_csv_sample(columns, rows, seed=seed)
    if error:
        return JSONResponse({"error": error}, status_code=400)

    csv_text = result.get("csv", "")
    headers = {"Content-Disposition": "attachment; filename=sample.csv"}
    return StreamingResponse(
        io.BytesIO(csv_text.encode("utf-8")),
        media_type="text/csv",
        headers=headers,
    )
