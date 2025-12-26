from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.qrverify.core.decode import decode_input
from modules.qrverify.core.verify import verify_decoded

app = FastAPI(title="QR Verify")

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

SECRET = os.getenv("QRFORGE_SECRET", "dev-secret")
FORGE_URL = os.getenv("QRFORGE_URL")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
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
