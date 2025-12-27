from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from modules.qrforge.core.ids import generate_public_id
from modules.qrforge.core.payload import build_identity_payload
from modules.qrforge.core.sign import sign_payload
from modules.qrforge.core.render import render_qr
from universe.flows import resolve_flow_links
from universe.settings import shared_templates_dir

app = FastAPI(title="QR Forge")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
SHARED_TEMPLATES = shared_templates_dir(ROOT_DIR)
templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
templates.env.auto_reload = True
templates.env.cache = {}
BRAND_DIR = ROOT_DIR / "brand"

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

SECRET = os.getenv("QRFORGE_SECRET", "dev-secret")
FLOW_BASE_URL = os.getenv("SPARKY_FLOW_BASE_URL")
OUTPUT = BASE_DIR / "qr.png"


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    flow_links = resolve_flow_links("qrforge", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/qr")
def create_qr(
    name: str = Form(None),
    supplier: str = Form(None),
    supplier_sku: str = Form(None),
):
    public_id = generate_public_id()

    payload = build_identity_payload(
        public_id=public_id,
        name=name,
        supplier=supplier,
        supplier_sku=supplier_sku,
    )

    signature = sign_payload(payload, SECRET)
    render_qr(payload, signature, str(OUTPUT))

    return FileResponse(
        OUTPUT,
        media_type="image/png",
        filename="qr.png",
    )
