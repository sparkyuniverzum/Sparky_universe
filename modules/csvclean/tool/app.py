from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.csvclean.core.clean import clean_csv_text, parse_output_delimiter
from universe.flows import resolve_flow_links
from universe.settings import configure_templates, shared_templates_dir
from universe.ads import attach_ads_globals

app = FastAPI(title="CSV Cleaner")

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
    flow_links = resolve_flow_links("csvclean", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/clean")
async def clean_csv(
    file: UploadFile | None = File(None),
    trim_cells: bool = Form(False),
    remove_empty_rows: bool = Form(False),
    delimiter: str | None = Form("auto"),
):
    if not file:
        return JSONResponse({"error": "Upload a CSV file."}, status_code=400)

    output_delimiter, error = parse_output_delimiter(delimiter)
    if error:
        return JSONResponse({"error": error}, status_code=400)

    raw_bytes = await file.read()
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    output_text, kept, removed, error = clean_csv_text(
        raw_text,
        trim_cells=trim_cells,
        remove_empty_rows=remove_empty_rows,
        output_delimiter=output_delimiter,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)

    headers = {
        "Content-Disposition": "attachment; filename=cleaned.csv",
        "X-Row-Count": str(kept),
        "X-Removed-Count": str(removed),
    }
    return StreamingResponse(
        io.BytesIO(output_text.encode("utf-8")),
        media_type="text/csv",
        headers=headers,
    )
