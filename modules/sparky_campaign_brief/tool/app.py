from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_campaign_brief.core.brief import build_campaign_brief
from universe.settings import shared_templates_dir

app = FastAPI(title="Sparky Campaign Brief Planet")

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
    campaign_name: str | None = Form(None),
    objective: str | None = Form(None),
    deadline: str | None = Form(None),
    success_metric: str | None = Form(None),
    target: str | None = Form(None),
    audience: str | None = Form(None),
    offer: str | None = Form(None),
    key_message: str | None = Form(None),
    tone: str | None = Form(None),
    cta: str | None = Form(None),
    channels: str | None = Form(None),
    deliverables: str | None = Form(None),
    proof_points: str | None = Form(None),
    constraints: str | None = Form(None),
    budget: str | None = Form(None),
):
    payload, error = build_campaign_brief(
        campaign_name=campaign_name,
        objective=objective,
        deadline=deadline,
        success_metric=success_metric,
        target=target,
        audience=audience,
        offer=offer,
        key_message=key_message,
        tone=tone,
        cta=cta,
        channels=channels,
        deliverables=deliverables,
        proof_points=proof_points,
        constraints=constraints,
        budget=budget,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
