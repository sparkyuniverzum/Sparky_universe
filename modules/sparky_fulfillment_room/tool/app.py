from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_fulfillment_room.core.fulfillment import (
    calculate_batch_id,
    calculate_labels,
    calculate_missing,
    calculate_slots,
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
    orders_labels: str | None = Form(None),
    orders_slots: str | None = Form(None),
    slots: str | None = Form(None),
    batch_name: str | None = Form(None),
    batch_date: str | None = Form(None),
    planned_items: str | None = Form(None),
    current_items: str | None = Form(None),
):
    if intent == "labels":
        payload, error = calculate_labels(orders_labels)
    elif intent == "slot_split":
        payload, error = calculate_slots(orders_slots, slots)
    elif intent == "batch_id":
        payload, error = calculate_batch_id(batch_name, batch_date)
    elif intent == "missing_check":
        payload, error = calculate_missing(planned_items, current_items)
    else:
        payload, error = None, "Unsupported intent."

    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
