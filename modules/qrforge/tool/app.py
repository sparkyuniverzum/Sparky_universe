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

app = FastAPI(title="QR Forge")

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

SECRET = os.getenv("QRFORGE_SECRET", "dev-secret")
FLOW_VERIFY_URL = os.getenv("SPARKY_FLOW_VERIFY_URL")
FLOW_BATCH_URL = os.getenv("SPARKY_FLOW_BATCH_URL")
OUTPUT = BASE_DIR / "qr.png"


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    flow_links = []
    if FLOW_VERIFY_URL:
        flow_links.append({"label": "Verify this QR", "href": FLOW_VERIFY_URL})
    if FLOW_BATCH_URL:
        flow_links.append({"label": "Batch-generate QR codes", "href": FLOW_BATCH_URL})

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links},
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
