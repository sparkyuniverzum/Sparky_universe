from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.qrverify.core.decode import decode_input
from modules.qrverify.core.verify import verify_decoded
from universe.flows import resolve_flow_links

app = FastAPI(title="QR Verify")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
SHARED_TEMPLATES = ROOT_DIR / "universe" / "templates"
templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
templates.env.auto_reload = True
templates.env.cache = {}
BRAND_DIR = ROOT_DIR / "brand"

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

SECRET = os.getenv("QRFORGE_SECRET", "dev-secret")
FORGE_URL = os.getenv("QRFORGE_URL")
FLOW_BASE_URL = os.getenv("SPARKY_FLOW_BASE_URL")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    flow_links = resolve_flow_links("qrverify", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links},
    )


@app.post("/verify")
async def verify_qr(
    file: UploadFile | None = File(None),
    payload: str | None = Form(None),
):
    file_bytes = await file.read() if file else None
    decoded, error = decode_input(file_bytes, payload)
    if error:
        return {"valid": False, "error": error}

    return verify_decoded(decoded, secret=SECRET, forge_url=FORGE_URL)
