from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.structure_format_translator.core.translate import translate_payload
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="Structure / Format Translator")

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
    flow_links = resolve_flow_links("structure_format_translator", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/translate")
async def translate(
    file: UploadFile | None = File(None),
    raw_text: str | None = Form(None),
    output_format: str = Form("json"),
):
    if not file and not (raw_text and raw_text.strip()):
        return JSONResponse({"error": "Upload a file or paste data."}, status_code=400)

    payload_input: str | bytes = raw_text or ""
    filename = None
    content_type = None
    if file is not None:
        filename = file.filename
        content_type = file.content_type
        payload_input = await file.read()

    payload, error, media_type = translate_payload(
        payload_input,
        filename=filename,
        content_type=content_type,
        output_format=output_format,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    if isinstance(payload, (bytes, bytearray)):
        filename_out = "translated.xlsx"
        return StreamingResponse(
            io.BytesIO(payload),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename_out}"'},
        )
    return payload
