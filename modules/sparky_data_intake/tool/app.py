from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_data_intake.core.brief import build_data_intake_brief
from universe.settings import shared_templates_dir

app = FastAPI(title="Sparky Data Intake Planet")

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


@app.post("/build")
def build(
    dataset_name: str | None = Form(None),
    purpose: str | None = Form(None),
    source_system: str | None = Form(None),
    data_format: str | None = Form(None),
    refresh_cadence: str | None = Form(None),
    delivery_method: str | None = Form(None),
    deadline: str | None = Form(None),
    volume_estimate: str | None = Form(None),
    included_entities: str | None = Form(None),
    exclusions: str | None = Form(None),
    key_fields: str | None = Form(None),
    identifiers: str | None = Form(None),
    time_fields: str | None = Form(None),
    transformations: str | None = Form(None),
    quality_risks: str | None = Form(None),
    missing_rules: str | None = Form(None),
    access_constraints: str | None = Form(None),
    privacy_notes: str | None = Form(None),
    next_action: str | None = Form(None),
    owner: str | None = Form(None),
    contact: str | None = Form(None),
    notes: str | None = Form(None),
):
    payload, error = build_data_intake_brief(
        dataset_name=dataset_name,
        purpose=purpose,
        source_system=source_system,
        data_format=data_format,
        refresh_cadence=refresh_cadence,
        delivery_method=delivery_method,
        deadline=deadline,
        volume_estimate=volume_estimate,
        included_entities=included_entities,
        exclusions=exclusions,
        key_fields=key_fields,
        identifiers=identifiers,
        time_fields=time_fields,
        transformations=transformations,
        quality_risks=quality_risks,
        missing_rules=missing_rules,
        access_constraints=access_constraints,
        privacy_notes=privacy_notes,
        next_action=next_action,
        owner=owner,
        contact=contact,
        notes=notes,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
