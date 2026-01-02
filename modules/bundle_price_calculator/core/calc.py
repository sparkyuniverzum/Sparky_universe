from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple


def _parse_decimal(value: str) -> Decimal | None:
    cleaned = value.strip().replace(" ", "")
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _parse_list(raw: str | None) -> List[Decimal]:
    if not raw:
        return []
    values: List[Decimal] = []
    for chunk in raw.replace("\n", ",").split(","):
        parsed = _parse_decimal(chunk)
        if parsed is None:
            continue
        values.append(parsed)
    return values


def bundle_price(
    items_raw: str | None,
    discount_percent: str | None,
    discount_amount: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    items = _parse_list(items_raw)
    if not items:
        return None, "Enter item prices."

    base_total = sum(items, Decimal("0"))
    discount = Decimal("0")

    if discount_percent and discount_percent.strip():
        percent = _parse_decimal(discount_percent)
        if percent is None:
            return None, "Discount percent must be a number."
        discount = (base_total * percent / Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    elif discount_amount and discount_amount.strip():
        discount = _parse_decimal(discount_amount) or Decimal("0")

    final_total = (base_total - discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if final_total < 0:
        return None, "Discount exceeds total."

    return {
        "items": [str(item) for item in items],
        "base_total": str(base_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "discount": str(discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "final_total": str(final_total),
    }, None
