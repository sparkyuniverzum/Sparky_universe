from __future__ import annotations

from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_CEILING,
    ROUND_FLOOR,
    ROUND_HALF_UP,
)
from typing import Any, Dict, Tuple


def _parse_decimal(value: Any, *, label: str) -> Tuple[Decimal | None, str | None]:
    if value is None:
        return None, f"{label} is required."
    raw = str(value).strip()
    if not raw:
        return None, f"{label} is required."

    compact = raw.replace(" ", "")
    if "," in compact and "." in compact:
        last_comma = compact.rfind(",")
        last_dot = compact.rfind(".")
        if last_comma > last_dot:
            compact = compact.replace(".", "")
            compact = compact.replace(",", ".")
        else:
            compact = compact.replace(",", "")
    elif "," in compact:
        compact = compact.replace(",", ".")

    try:
        return Decimal(compact), None
    except (InvalidOperation, ValueError):
        return None, "Invalid number format."


def _quantize(value: Decimal, decimals: int = 2) -> str:
    decimals = max(0, min(int(decimals), 6))
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def _round_to_step(value: Decimal, step: Decimal, mode: str) -> Decimal:
    ratio = value / step
    if mode == "up":
        rounded = ratio.quantize(Decimal("1"), rounding=ROUND_CEILING)
    elif mode == "down":
        rounded = ratio.quantize(Decimal("1"), rounding=ROUND_FLOOR)
    else:
        rounded = ratio.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return rounded * step


def calculate_cash_rounding(
    amount: Any,
    step: Any,
    *,
    mode: str = "nearest",
    paid: Any | None = None,
    decimals: int = 2,
) -> Tuple[Dict[str, str] | None, str | None]:
    amount_dec, error = _parse_decimal(amount, label="Amount")
    if error or amount_dec is None:
        return None, error

    step_dec, error = _parse_decimal(step, label="Step")
    if error or step_dec is None:
        return None, error

    if amount_dec < Decimal("0"):
        return None, "Amount must be zero or higher."
    if step_dec <= Decimal("0"):
        return None, "Step must be greater than zero."

    mode_key = mode.lower().strip()
    if mode_key not in {"nearest", "up", "down"}:
        return None, "Unknown rounding mode."

    rounded_total = _round_to_step(amount_dec, step_dec, mode_key)
    delta = rounded_total - amount_dec

    paid_dec = None
    change = None
    if paid is not None and str(paid).strip() != "":
        paid_dec, error = _parse_decimal(paid, label="Paid")
        if error or paid_dec is None:
            return None, error
        if paid_dec < rounded_total:
            return None, "Paid amount must cover the rounded total."
        change = paid_dec - rounded_total

    return {
        "amount": _quantize(amount_dec, decimals),
        "step": _quantize(step_dec, decimals),
        "mode": mode_key,
        "rounded_total": _quantize(rounded_total, decimals),
        "delta": _quantize(delta, decimals),
        "paid": _quantize(paid_dec, decimals) if paid_dec is not None else "",
        "change": _quantize(change, decimals) if change is not None else "",
    }, None
