from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.json_linter.core.lint import lint_json
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir
from universe.ads import attach_ads_globals

app = FastAPI(title="JSON Linter")

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
    flow_links = resolve_flow_links("json_linter", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/lint")
def lint(
    json_text: str | None = Form(None),
    indent: str | None = Form("2"),
    sort_keys: bool = Form(False),
):
    try:
        indent_int = int(str(indent).strip())
    except ValueError:
        return JSONResponse({"error": "Indent must be a whole number."}, status_code=400)
    indent_int = max(0, min(indent_int, 8))
    result, error = lint_json(json_text, indent=indent_int, sort_keys=sort_keys)
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
