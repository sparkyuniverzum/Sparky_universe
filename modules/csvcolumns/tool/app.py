from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.csvcolumns.core.extract import extract_csv_text, parse_column_indexes
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="CSV Column Extractor")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
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
    flow_links = resolve_flow_links("csvcolumns", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/extract")
async def extract_columns(
    file: UploadFile | None = File(None),
    columns: str | None = Form(None),
    has_header: bool = Form(False),
):
    if not file:
        return JSONResponse({"error": "Upload a CSV file."}, status_code=400)

    column_indexes, error = parse_column_indexes(columns)
    if error:
        return JSONResponse({"error": error}, status_code=400)

    raw_bytes = await file.read()
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    output_text, extracted, error = extract_csv_text(
        raw_text, columns=column_indexes, has_header=has_header
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)

    headers = {
        "Content-Disposition": "attachment; filename=columns.csv",
        "X-Row-Count": str(extracted),
        "X-Column-Count": str(len(column_indexes)),
    }
    return StreamingResponse(
        io.BytesIO(output_text.encode("utf-8")),
        media_type="text/csv",
        headers=headers,
    )
