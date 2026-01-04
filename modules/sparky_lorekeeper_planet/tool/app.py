from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_lorekeeper_planet.core.fragment import (
    list_fragments,
    load_fragment,
    resolve_tone,
    tone_options,
)
from universe.settings import shared_templates_dir

app = FastAPI(title="Sparky Lorekeeper Planet")

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
        {
            "request": request,
            "base_path": base_path,
            "fragments": list_fragments(),
            "tones": tone_options(),
        },
    )


@app.post("/build")
def build(fragment: str = Form(...), tone: str = Form("mystic")):
    fragment_key = fragment.strip().lower()
    entry = load_fragment(fragment_key)
    if not entry:
        return JSONResponse({"error": "Fragment not found."}, status_code=400)
    sigil = resolve_tone(tone.strip().lower())
    return {
        "key": entry.key,
        "title": entry.title,
        "subtitle": entry.subtitle,
        "label": entry.label,
        "fragment": entry.text,
        "sigil": sigil,
    }
