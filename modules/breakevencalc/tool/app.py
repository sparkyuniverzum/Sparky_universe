from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.breakevencalc.core.break_even import calculate_break_even
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="Break-even Calculator")

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
    flow_links = resolve_flow_links("breakevencalc", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/calc")
def calc_break_even(
    fixed_costs: str | None = Form(None),
    price: str | None = Form(None),
    variable_cost: str | None = Form(None),
    decimals: int = Form(2),
):
    result, error = calculate_break_even(
        fixed_costs, price, variable_cost, decimals=decimals
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
