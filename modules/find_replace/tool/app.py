from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.find_replace.core.replace import replace_text
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir
from universe.ads import attach_ads_globals

app = FastAPI(title="Find & Replace")

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
    flow_links = resolve_flow_links("find_replace", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/replace")
def replace(
    text: str | None = Form(None),
    find: str | None = Form(None),
    replace_with: str | None = Form(""),
    use_regex: bool = Form(False),
    ignore_case: bool = Form(False),
    max_replacements: str | None = Form("0"),
):
    try:
        max_int = int(str(max_replacements).strip())
    except ValueError:
        return JSONResponse({"error": "Max replacements must be a number."}, status_code=400)
    max_int = max(0, min(max_int, 5000))
    result, error = replace_text(
        text,
        find,
        replace_with,
        use_regex=use_regex,
        ignore_case=ignore_case,
        max_replacements=max_int,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
