from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_support_triage.core.brief import build_triage_brief
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="Sparky Support Triage Planet")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"
SHARED_TEMPLATES = shared_templates_dir(ROOT_DIR)

templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
configure_templates(templates)

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
    issue_title: str | None = Form(None),
    reported_by: str | None = Form(None),
    report_time: str | None = Form(None),
    severity: str | None = Form(None),
    impact_scope: str | None = Form(None),
    user_impact: str | None = Form(None),
    affected_product: str | None = Form(None),
    environment: str | None = Form(None),
    symptoms: str | None = Form(None),
    reproduction: str | None = Form(None),
    recent_changes: str | None = Form(None),
    logs: str | None = Form(None),
    workarounds: str | None = Form(None),
    owner: str | None = Form(None),
    next_action: str | None = Form(None),
    comms_plan: str | None = Form(None),
    constraints: str | None = Form(None),
):
    payload, error = build_triage_brief(
        issue_title=issue_title,
        reported_by=reported_by,
        report_time=report_time,
        severity=severity,
        impact_scope=impact_scope,
        user_impact=user_impact,
        affected_product=affected_product,
        environment=environment,
        symptoms=symptoms,
        reproduction=reproduction,
        recent_changes=recent_changes,
        logs=logs,
        workarounds=workarounds,
        owner=owner,
        next_action=next_action,
        comms_plan=comms_plan,
        constraints=constraints,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
