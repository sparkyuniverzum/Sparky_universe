from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.qr_batch.core.batch import build_batch_zip
from modules.sparky_core.core.secrets import require_secret
from universe.flows import resolve_flow_links
from universe.settings import configure_templates, shared_templates_dir
from universe.ads import attach_ads_globals

app = FastAPI(title="QR Batch")

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
SECRET = require_secret("QRFORGE_SECRET")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    flow_links = resolve_flow_links("qr_batch", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/batch")
def create_batch(items: str | None = Form(None)):
    if not items or not items.strip():
        return JSONResponse(
            {"error": "Provide at least one CSV line."},
            status_code=400,
        )

    zip_bytes, count, error = build_batch_zip(items, secret=SECRET)
    if error:
        return JSONResponse(
            {"error": error},
            status_code=400,
        )
    if count == 0:
        return JSONResponse(
            {"error": "No valid rows found."},
            status_code=400,
        )

    headers = {
        "Content-Disposition": "attachment; filename=qr-batch.zip",
        "X-QR-Count": str(count),
    }
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers=headers,
    )
