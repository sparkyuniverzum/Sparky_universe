from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.moneyformat.core.format import format_money
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="Money Formatter")

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
    flow_links = resolve_flow_links("moneyformat", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/format")
def format_value(
    value: str | None = Form(None),
    decimals: int = Form(2),
    thousand_sep: str = Form(" "),
    decimal_sep: str = Form(","),
    currency: str = Form("CZK"),
    position: str = Form("suffix"),
):
    result, error = format_money(
        value,
        decimals=decimals,
        thousand_sep=thousand_sep,
        decimal_sep=decimal_sep,
        currency=currency,
        position=position,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
