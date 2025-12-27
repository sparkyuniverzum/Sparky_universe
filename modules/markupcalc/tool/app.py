from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.markupcalc.core.markup import calculate_markup, calculate_price_from_markup
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="Markup Calculator")

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
    flow_links = resolve_flow_links("markupcalc", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/markup")
def markup_from_price(
    cost: str | None = Form(None),
    price: str | None = Form(None),
    decimals: int = Form(2),
):
    result, error = calculate_markup(cost, price, decimals=decimals)
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result


@app.post("/price")
def price_from_markup(
    cost: str | None = Form(None),
    markup_percent: str | None = Form(None),
    decimals: int = Form(2),
):
    result, error = calculate_price_from_markup(
        cost, markup_percent, decimals=decimals
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
