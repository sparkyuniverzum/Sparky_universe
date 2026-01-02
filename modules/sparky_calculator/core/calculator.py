from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple


@dataclass
class ResultBlock:
    label: str
    value: float
    unit: str | None = None


def _parse_decimal(value: str | None, name: str, minimum: Decimal | None) -> Tuple[Decimal | None, str | None]:
    if value is None or str(value).strip() == "":
        return None, f"{name} is required."
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None, f"{name} must be a number."
    if minimum is not None and parsed < minimum:
        return None, f"{name} must be at least {minimum}."
    return parsed, None


def _parse_int(value: str | None, name: str, minimum: int) -> Tuple[int | None, str | None]:
    if value is None or str(value).strip() == "":
        return None, f"{name} is required."
    try:
        parsed = int(str(value))
    except ValueError:
        return None, f"{name} must be a whole number."
    if parsed < minimum:
        return None, f"{name} must be at least {minimum}."
    return parsed, None


def _quantize(value: Decimal, places: int) -> Decimal:
    scale = Decimal("1").scaleb(-places)
    return value.quantize(scale, rounding=ROUND_HALF_UP)


def _as_float(value: Decimal, places: int = 2) -> float:
    return float(_quantize(value, places))


def _as_text(value: Decimal, places: int = 2) -> str:
    return f"{_quantize(value, places):.{places}f}"


def _make_payload(
    *,
    intent: str,
    primary: ResultBlock,
    secondary: List[ResultBlock],
    sparky_line: str,
) -> Dict[str, Any]:
    return {
        "intent": intent,
        "primary": {
            "label": primary.label,
            "value": primary.value,
            "unit": primary.unit,
        },
        "secondary": [
            {"label": item.label, "value": item.value, "unit": item.unit}
            for item in secondary
        ],
        "sparky": sparky_line,
    }


def calculate_monthly_balance(
    income_raw: str | None,
    expenses_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    income, error = _parse_decimal(income_raw, "Income", Decimal("0.01"))
    if error:
        return None, error
    expenses, error = _parse_decimal(expenses_raw, "Expenses", Decimal("0"))
    if error:
        return None, error

    balance = income - expenses
    share = (expenses / income) * Decimal("100")

    primary = ResultBlock("Monthly balance", _as_float(balance))
    secondary = [ResultBlock("Expense share", _as_float(share, 1), "%")]
    sparky_line = f"Monthly balance: {_as_text(balance)}."
    return _make_payload(
        intent="monthly_balance",
        primary=primary,
        secondary=secondary,
        sparky_line=sparky_line,
    ), None


def calculate_margin(
    price_raw: str | None,
    cost_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    price, error = _parse_decimal(price_raw, "Price", Decimal("0.01"))
    if error:
        return None, error
    cost, error = _parse_decimal(cost_raw, "Cost", Decimal("0"))
    if error:
        return None, error

    profit = price - cost
    margin = (profit / price) * Decimal("100")

    primary = ResultBlock("Margin", _as_float(margin, 1), "%")
    secondary = [ResultBlock("Profit per unit", _as_float(profit))]
    sparky_line = f"Margin: {_as_text(margin, 1)}%."
    return _make_payload(
        intent="margin",
        primary=primary,
        secondary=secondary,
        sparky_line=sparky_line,
    ), None


def calculate_target_price(
    target_profit_raw: str | None,
    cost_raw: str | None,
    fee_percent_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    target_profit, error = _parse_decimal(target_profit_raw, "Target profit", Decimal("0"))
    if error:
        return None, error
    cost, error = _parse_decimal(cost_raw, "Cost", Decimal("0"))
    if error:
        return None, error
    fee_percent, error = _parse_decimal(fee_percent_raw, "Fee percent", Decimal("0"))
    if error:
        return None, error
    if fee_percent >= Decimal("100"):
        return None, "Fee percent must be below 100."

    fee_rate = fee_percent / Decimal("100")
    denominator = Decimal("1") - fee_rate
    if denominator <= Decimal("0"):
        return None, "Fee percent must be below 100."

    price = (cost + target_profit) / denominator
    net_profit = (price * denominator) - cost

    primary = ResultBlock("Recommended price", _as_float(price))
    secondary = [ResultBlock("Expected net profit", _as_float(net_profit))]
    sparky_line = f"Recommended price: {_as_text(price)}."
    return _make_payload(
        intent="target_price",
        primary=primary,
        secondary=secondary,
        sparky_line=sparky_line,
    ), None


def calculate_split_amount(
    total_raw: str | None,
    people_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    total, error = _parse_decimal(total_raw, "Total amount", Decimal("0"))
    if error:
        return None, error
    people, error = _parse_int(people_raw, "People", 1)
    if error:
        return None, error

    per_person = _quantize(total / Decimal(people), 2)
    remainder = _quantize(total - (per_person * Decimal(people)), 2)
    if remainder < 0:
        remainder = Decimal("0")

    primary = ResultBlock("Per person", float(per_person))
    secondary = [ResultBlock("Remainder", float(remainder))]
    sparky_line = f"Each person gets {_as_text(per_person)}."
    return _make_payload(
        intent="split_amount",
        primary=primary,
        secondary=secondary,
        sparky_line=sparky_line,
    ), None
