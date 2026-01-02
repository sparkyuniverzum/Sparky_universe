from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_fulfillment_room.core.fulfillment import (
    calculate_cutoff,
    calculate_packaging_buffer,
    calculate_packer_need,
    calculate_pick_list,
)
from universe.settings import shared_templates_dir

app = FastAPI(title="Sparky Fulfillment Room")

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


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "base_path": base_path},
    )


@app.post("/calculate")
def calculate(
    intent: str = Form(...),
    orders_packers: str | None = Form(None),
    minutes_per_order: str | None = Form(None),
    hours_available: str | None = Form(None),
    orders_left: str | None = Form(None),
    minutes_per_order_cutoff: str | None = Form(None),
    packers_available: str | None = Form(None),
    hours_left: str | None = Form(None),
    orders_pick: str | None = Form(None),
    items_per_order: str | None = Form(None),
    orders_packaging: str | None = Form(None),
    buffer_percent: str | None = Form(None),
):
    if intent == "packer_need":
        payload, error = calculate_packer_need(
            orders_packers,
            minutes_per_order,
            hours_available,
        )
    elif intent == "cutoff_check":
        payload, error = calculate_cutoff(
            orders_left,
            minutes_per_order_cutoff,
            packers_available,
            hours_left,
        )
    elif intent == "pick_list":
        payload, error = calculate_pick_list(orders_pick, items_per_order)
    elif intent == "packaging":
        payload, error = calculate_packaging_buffer(orders_packaging, buffer_percent)
    else:
        payload, error = None, "Unsupported intent."

    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
