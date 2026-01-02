from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.placeholder_finder.core.find import find_placeholders
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="Placeholder Finder")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"
SHARED_TEMPLATES = shared_templates_dir(ROOT_DIR)
MAX_BYTES = 4 * 1024 * 1024

templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
templates.env.auto_reload = True
templates.env.cache = {}
attach_ads_globals(templates)

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

FLOW_BASE_URL = os.getenv("SPARKY_FLOW_BASE_URL")


async def _read_text(
    file: UploadFile | None,
    raw_text: str | None,
) -> tuple[str | None, str | None]:
    if file is not None:
        data = await file.read()
        if len(data) > MAX_BYTES:
            return None, "File exceeds 4 MB."
        return data.decode("utf-8", errors="replace"), None
    if raw_text and raw_text.strip():
        if len(raw_text.encode("utf-8")) > MAX_BYTES:
            return None, "Text exceeds 4 MB."
        return raw_text, None
    return None, "Upload a file or paste text."


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    flow_links = resolve_flow_links("placeholder_finder", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/find")
async def find(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
):
    resolved, error = await _read_text(file, text)
    if error:
        return JSONResponse({"error": error}, status_code=400)

    payload, error = find_placeholders(resolved)
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
