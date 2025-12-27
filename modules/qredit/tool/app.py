from __future__ import annotations

import os
from pathlib import Path

import io

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.qredit.core.edit import decode_to_payload, parse_payload_json, render_qr_bytes
from modules.qrforge.core.sign import sign_payload
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="QR Edit")

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
SECRET = os.getenv("QRFORGE_SECRET", "dev-secret")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    flow_links = resolve_flow_links("qredit", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/decode")
async def decode_qr(
    file: UploadFile | None = File(None),
    payload: str | None = Form(None),
):
    file_bytes = await file.read() if file else None
    result, error = decode_to_payload(file_bytes, payload)
    if error:
        return JSONResponse({"error": error}, status_code=400)

    return result


@app.post("/qr")
def render_qr(payload_json: str | None = Form(None)):
    payload, error = parse_payload_json(payload_json)
    if error:
        return JSONResponse({"error": error}, status_code=400)

    signature = sign_payload(payload, SECRET)
    png_bytes = render_qr_bytes(payload, signature)
    headers = {"Content-Disposition": "attachment; filename=qr-edit.png"}
    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers=headers,
    )
