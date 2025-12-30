from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, Tuple


def _parse_decimal(value: object, *, label: str) -> Tuple[Decimal | None, str | None]:
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
        return None, f"{label} must be a number."


def _parse_int(value: object, *, label: str, default: int) -> Tuple[int, str | None]:
    if value is None:
        return default, None
    raw = str(value).strip()
    if not raw:
        return default, None
    try:
        return int(raw), None
    except ValueError:
        return default, f"{label} must be a whole number."


def _quantize(value: Decimal, decimals: int) -> str:
    quant = Decimal("1") if decimals == 0 else Decimal("1." + "0" * decimals)
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def compute_fee(
    amount: object,
    percent_fee: object,
    fixed_fee: object,
    *,
    mode: object = "gross_from_net",
    decimals: object = 2,
) -> Tuple[Dict[str, object] | None, str | None]:
    amount_dec, error = _parse_decimal(amount, label="Amount")
    if error or amount_dec is None:
        return None, error
    percent_dec, error = _parse_decimal(percent_fee, label="Percent fee")
    if error or percent_dec is None:
        return None, error
    fixed_dec, error = _parse_decimal(fixed_fee, label="Fixed fee")
    if error or fixed_dec is None:
        return None, error

    if amount_dec < Decimal("0"):
        return None, "Amount must be non-negative."
    if percent_dec < Decimal("0") or fixed_dec < Decimal("0"):
        return None, "Fees must be non-negative."

    decimals_int, error = _parse_int(decimals, label="Decimals", default=2)
    if error:
        return None, error
    if decimals_int < 0 or decimals_int > 4:
        return None, "Decimals must be between 0 and 4."

    rate = percent_dec / Decimal("100")
    if rate >= Decimal("1"):
        return None, "Percent fee must be below 100."

    mode_key = str(mode or "gross_from_net").strip().lower()
    if mode_key not in {"gross_from_net", "net_from_gross"}:
        return None, "Mode must be gross_from_net or net_from_gross."

    if mode_key == "gross_from_net":
        net = amount_dec
        gross = (net + fixed_dec) / (Decimal("1") - rate)
    else:
        gross = amount_dec
        net = gross * (Decimal("1") - rate) - fixed_dec

    if net < Decimal("0"):
        return None, "Net amount is negative with the given fees."

    fee_total = gross - net

    return {
        "mode": mode_key,
        "gross": _quantize(gross, decimals_int),
        "net": _quantize(net, decimals_int),
        "fee_total": _quantize(fee_total, decimals_int),
        "percent_fee": _quantize(percent_dec, 2),
        "fixed_fee": _quantize(fixed_dec, decimals_int),
    }, None
