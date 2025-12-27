from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Path as PathParam, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.unitconvert.core.units import convert_value, list_units
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="Unit Converter")

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


def _pair_from_path(pair: str | None) -> tuple[str | None, str | None]:
    if not pair:
        return None, None
    if "-to-" not in pair:
        return None, None
    from_unit, to_unit = pair.split("-to-", 1)
    return from_unit.strip(), to_unit.strip()


def _render_index(request: Request, pair: str | None = None):
    base_path = request.scope.get("root_path", "")
    flow_links = resolve_flow_links("unitconvert", base_url=FLOW_BASE_URL)
    from_unit, to_unit = _pair_from_path(pair)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "flow_links": flow_links,
            "base_path": base_path or "/convert",
            "units": list_units(),
            "from_unit": from_unit,
            "to_unit": to_unit,
            "pair": pair,
        },
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return _render_index(request)


@app.get("/unit", response_class=HTMLResponse)
def index_unit(request: Request):
    return _render_index(request)


@app.get("/{pair}", response_class=HTMLResponse)
def index_pair(request: Request, pair: str = PathParam(pattern=r".+-to-.+")):
    return _render_index(request, pair=pair)


@app.post("/convert")
def convert(
    value: str | None = Form(None),
    from_unit: str = Form("m"),
    to_unit: str = Form("cm"),
    decimals: int = Form(6),
):
    result, error = convert_value(value, from_unit, to_unit, decimals=decimals)
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return result
