from __future__ import annotations

import os
from pathlib import Path

import io

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.csvnormalize.core.normalize import normalize_csv_text
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="CSV Number Normalizer")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[3]
BRAND_DIR = ROOT_DIR / "brand"
SHARED_TEMPLATES = shared_templates_dir(ROOT_DIR)

templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
templates.env.auto_reload = True
templates.env.cache = {}

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

FLOW_BASE_URL = os.getenv("SPARKY_FLOW_BASE_URL")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    flow_links = resolve_flow_links("csvnormalize", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/normalize")
async def normalize_csv(
    file: UploadFile | None = File(None),
    column: str | None = Form(None),
):
    if not file:
        return JSONResponse({"error": "Upload a CSV file."}, status_code=400)

    column_index = 0
    if column and column.strip():
        try:
            column_index = max(int(column) - 1, 0)
        except ValueError:
            return JSONResponse({"error": "Column must be a number."}, status_code=400)

    raw_bytes = await file.read()
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    output_text, count = normalize_csv_text(raw_text, column_index=column_index)
    if not output_text:
        return JSONResponse({"error": "CSV is empty or invalid."}, status_code=400)

    headers = {
        "Content-Disposition": "attachment; filename=normalized.csv",
        "X-Normalized-Count": str(count),
    }
    return StreamingResponse(
        io.BytesIO(output_text.encode("utf-8")),
        media_type="text/csv",
        headers=headers,
    )
