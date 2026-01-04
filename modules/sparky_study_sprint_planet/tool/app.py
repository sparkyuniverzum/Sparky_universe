from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_study_sprint_planet.core.brief import build_sprint_plan
from universe.settings import configure_templates, shared_templates_dir

app = FastAPI(title="Sparky Study Sprint Planet")

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
    goal: str | None = Form(None),
    days: str | None = Form(None),
    minutes_per_day: str | None = Form(None),
    session_length: str | None = Form(None),
    buffer_days: str | None = Form(None),
    review_blocks_per_day: str | None = Form(None),
    topics: str | None = Form(None),
):
    payload, error = build_sprint_plan(
        goal=goal,
        days=days,
        minutes_per_day=minutes_per_day,
        session_length=session_length,
        buffer_days=buffer_days,
        review_blocks_per_day=review_blocks_per_day,
        topics=topics,
    )
    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
