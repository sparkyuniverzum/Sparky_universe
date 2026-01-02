from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple


def _parse_decimal(value: str | None) -> Tuple[Decimal | None, str | None]:
    if not value or not value.strip():
        return None, "Enter a price."
    try:
        cleaned = value.strip().replace(" ", "")
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        return Decimal(cleaned), None
    except (InvalidOperation, ValueError):
        return None, "Price must be a number."


def _parse_percent_list(raw: str | None) -> List[Decimal]:
    if not raw:
        return []
    items: List[Decimal] = []
    for chunk in raw.replace("%", "").split(","):
        value = chunk.strip()
        if not value:
            continue
        try:
            items.append(Decimal(value))
        except (InvalidOperation, ValueError):
            continue
    return items


def build_markdown_plan(
    base_price: str | None,
    *,
    discounts: str | None = None,
    start: int | None = None,
    step: int | None = None,
    count: int | None = None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    price, error = _parse_decimal(base_price)
    if error:
        return None, error
    assert price is not None

    percent_list = _parse_percent_list(discounts)
    if not percent_list:
        start = start if start is not None else 10
        step = step if step is not None else 10
        count = count if count is not None else 3
        percent_list = [Decimal(start + step * idx) for idx in range(count)]

    rows: List[Dict[str, Any]] = []
    for percent in percent_list:
        if percent < 0:
            continue
        discount_amount = (price * percent / Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        final_price = (price - discount_amount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        rows.append(
            {
                "discount_percent": float(percent),
                "discount_amount": str(discount_amount),
                "final_price": str(final_price),
            }
        )

    return {
        "base_price": str(price),
        "rows": rows,
        "count": len(rows),
    }, None
