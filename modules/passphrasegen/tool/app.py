from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.passphrasegen.core.generate import generate_passphrases
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="Passphrase Generator")

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
    flow_links = resolve_flow_links("passphrasegen", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/generate")
def generate(
    words: str | None = Form(None),
    count: str | None = Form(None),
    separator: str | None = Form(None),
    caps: str | None = Form(None),
):
    result, error = generate_passphrases(
        words,
        count,
        separator=separator,
        caps=caps,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
