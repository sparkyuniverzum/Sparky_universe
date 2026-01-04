from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.og_preview.core.preview import validate_preview
from universe.ads import attach_ads_globals
from universe.flows import resolve_flow_links
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="OG Preview")

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
    flow_links = resolve_flow_links("og_preview", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


def _parse_int(value: str | None, label: str) -> tuple[int | None, str | None]:
    if value is None or value == "":
        return None, None
    try:
        number = int(value)
    except ValueError:
        return None, f"{label} must be a whole number."
    if number <= 0:
        return None, f"{label} must be greater than zero."
    return number, None


@app.post("/preview")
def preview(
    title: str | None = Form(None),
    description: str | None = Form(None),
    url: str | None = Form(None),
    image_url: str | None = Form(None),
    site_name: str | None = Form(None),
    twitter_handle: str | None = Form(None),
    image_width: str | None = Form(None),
    image_height: str | None = Form(None),
    card_type: str | None = Form(None),
):
    width, error = _parse_int(image_width, "Image width")
    if error:
        return JSONResponse({"error": error}, status_code=400)
    height, error = _parse_int(image_height, "Image height")
    if error:
        return JSONResponse({"error": error}, status_code=400)

    result, warnings = validate_preview(
        title=title,
        description=description,
        url=url,
        image_url=image_url,
        site_name=site_name,
        twitter_handle=twitter_handle,
        image_width=width,
        image_height=height,
        card_type=card_type,
    )
    return {**result, "warnings": warnings}
