from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.data_difference.core.diff import diff_datasets
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="Data Difference")

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
    flow_links = resolve_flow_links("data_difference", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/diff")
async def diff(
    file_a: UploadFile | None = File(None),
    file_b: UploadFile | None = File(None),
    key_columns: str | None = Form(None),
):
    if not file_a or not file_b:
        return JSONResponse({"error": "Upload two files to compare."}, status_code=400)

    data_a = await file_a.read()
    data_b = await file_b.read()
    payload, error = diff_datasets(
        data_a,
        data_b,
        filename_a=file_a.filename,
        filename_b=file_b.filename,
        content_type_a=file_a.content_type,
        content_type_b=file_b.content_type,
        key_columns=key_columns,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
