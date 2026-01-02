from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_launch_room.core.brief import build_launch_brief
from universe.settings import shared_templates_dir

app = FastAPI(title="Sparky Launch Room")

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
    launch_name: str | None = Form(None),
    release_type: str | None = Form(None),
    launch_date: str | None = Form(None),
    objective: str | None = Form(None),
    success_metric: str | None = Form(None),
    target: str | None = Form(None),
    audience: str | None = Form(None),
    value_prop: str | None = Form(None),
    key_message: str | None = Form(None),
    cta: str | None = Form(None),
    channels: str | None = Form(None),
    deliverables: str | None = Form(None),
    readiness: str | None = Form(None),
    dependencies: str | None = Form(None),
    risks: str | None = Form(None),
    mitigations: str | None = Form(None),
    owners: str | None = Form(None),
    approvals: str | None = Form(None),
    support_notes: str | None = Form(None),
    rollback_plan: str | None = Form(None),
):
    payload, error = build_launch_brief(
        launch_name=launch_name,
        release_type=release_type,
        launch_date=launch_date,
        objective=objective,
        success_metric=success_metric,
        target=target,
        audience=audience,
        value_prop=value_prop,
        key_message=key_message,
        cta=cta,
        channels=channels,
        deliverables=deliverables,
        readiness=readiness,
        dependencies=dependencies,
        risks=risks,
        mitigations=mitigations,
        owners=owners,
        approvals=approvals,
        support_notes=support_notes,
        rollback_plan=rollback_plan,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
