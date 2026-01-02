from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.sparky_calculator.core.calculator import (
    calculate_margin,
    calculate_monthly_balance,
    calculate_split_amount,
    calculate_target_price,
)

app = FastAPI(title="Sparky Calculator")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
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


@app.post("/calculate")
def calculate(
    intent: str = Form(...),
    income: str | None = Form(None),
    expenses: str | None = Form(None),
    price: str | None = Form(None),
    cost_margin: str | None = Form(None),
    target_profit: str | None = Form(None),
    cost_target: str | None = Form(None),
    fee_percent: str | None = Form(None),
    total_amount: str | None = Form(None),
    people: str | None = Form(None),
):
    if intent == "monthly_balance":
        payload, error = calculate_monthly_balance(income, expenses)
    elif intent == "margin":
        payload, error = calculate_margin(price, cost_margin)
    elif intent == "target_price":
        payload, error = calculate_target_price(target_profit, cost_target, fee_percent)
    elif intent == "split_amount":
        payload, error = calculate_split_amount(total_amount, people)
    else:
        payload, error = None, "Unsupported intent."

    if error:
        return JSONResponse({"error": error}, status_code=400)
    return payload
