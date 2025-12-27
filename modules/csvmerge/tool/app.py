from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.csvmerge.core.merge import merge_csv_text, parse_column_index
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="CSV Merger")

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
    flow_links = resolve_flow_links("csvmerge", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/merge")
async def merge_csv(
    left_file: UploadFile | None = File(None),
    right_file: UploadFile | None = File(None),
    left_key: str | None = Form(None),
    right_key: str | None = Form(None),
    has_headers: bool = Form(False),
):
    if not left_file or not right_file:
        return JSONResponse({"error": "Upload both CSV files."}, status_code=400)

    left_index, error = parse_column_index(left_key, label="Left")
    if error:
        return JSONResponse({"error": error}, status_code=400)

    right_index, error = parse_column_index(right_key, label="Right")
    if error:
        return JSONResponse({"error": error}, status_code=400)

    left_bytes = await left_file.read()
    right_bytes = await right_file.read()
    left_text = left_bytes.decode("utf-8", errors="replace")
    right_text = right_bytes.decode("utf-8", errors="replace")

    output_text, merged, unmatched, error = merge_csv_text(
        left_text,
        right_text,
        left_key=left_index,
        right_key=right_index,
        has_headers=has_headers,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)

    headers = {
        "Content-Disposition": "attachment; filename=merged.csv",
        "X-Merged-Count": str(merged),
        "X-Unmatched-Count": str(unmatched),
    }
    return StreamingResponse(
        io.BytesIO(output_text.encode("utf-8")),
        media_type="text/csv",
        headers=headers,
    )
