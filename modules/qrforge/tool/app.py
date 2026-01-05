from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from modules.qrforge.core.ids import generate_public_id
from modules.qrforge.core.payload import build_identity_payload
from modules.qrforge.core.sign import sign_payload
from modules.qrforge.core.render import render_qr_bytes
from modules.sparky_core.core.secrets import optional_secret
from universe.flows import resolve_flow_links
from universe.settings import configure_templates, shared_templates_dir
from universe.ads import attach_ads_globals

app = FastAPI(title="QR Forge")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
SHARED_TEMPLATES = shared_templates_dir(ROOT_DIR)
templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
configure_templates(templates)
attach_ads_globals(templates)
BRAND_DIR = ROOT_DIR / "brand"

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

FLOW_BASE_URL = os.getenv("SPARKY_FLOW_BASE_URL")


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
    secret, error = optional_secret("QRFORGE_SECRET")
    if error:
        return JSONResponse({"error": error}, status_code=503)
    public_id = generate_public_id()

    payload = build_identity_payload(
        public_id=public_id,
        name=name,
        supplier=supplier,
        supplier_sku=supplier_sku,
    )

    if secret is None:
        return JSONResponse({"error": "Secret is missing"}, status_code=503)
    signature = sign_payload(payload, secret)
    png_bytes = render_qr_bytes(payload, signature)
    headers = {"Content-Disposition": "attachment; filename=qr.png"}
    return Response(content=png_bytes, media_type="image/png", headers=headers)
