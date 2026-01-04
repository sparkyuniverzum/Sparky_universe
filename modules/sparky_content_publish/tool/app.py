from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_content_publish.core.brief import build_publish_brief
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="Sparky Content Publish Planet")

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
    title: str | None = Form(None),
    objective: str | None = Form(None),
    audience: str | None = Form(None),
    message: str | None = Form(None),
    cta: str | None = Form(None),
    channel: str | None = Form(None),
    format_type: str | None = Form(None),
    publish_date: str | None = Form(None),
    tone: str | None = Form(None),
    assets: str | None = Form(None),
    proof_points: str | None = Form(None),
    sources: str | None = Form(None),
    approvals: str | None = Form(None),
    constraints: str | None = Form(None),
    owner: str | None = Form(None),
):
    payload, error = build_publish_brief(
        title=title,
        objective=objective,
        audience=audience,
        message=message,
        cta=cta,
        channel=channel,
        format_type=format_type,
        publish_date=publish_date,
        tone=tone,
        assets=assets,
        proof_points=proof_points,
        sources=sources,
        approvals=approvals,
        constraints=constraints,
        owner=owner,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
