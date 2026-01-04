from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_misconception_planet.core.brief import build_misconception_brief
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="Sparky Misconception Planet")

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
    topic: str | None = Form(None),
    audience: str | None = Form(None),
    misconceptions: str | None = Form(None),
    corrections: str | None = Form(None),
    proof_points: str | None = Form(None),
    examples: str | None = Form(None),
    constraints: str | None = Form(None),
    owner: str | None = Form(None),
):
    payload, error = build_misconception_brief(
        topic=topic,
        audience=audience,
        misconceptions=misconceptions,
        corrections=corrections,
        proof_points=proof_points,
        examples=examples,
        constraints=constraints,
        owner=owner,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
