from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple

PAIR_RE = re.compile(r"([0-9.,]+)\s*(?:x|\*)\s*([0-9]+)")


def _parse_decimal(value: str) -> Decimal | None:
    cleaned = value.strip().replace(" ", "")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _parse_pairs(raw: str | None) -> List[Tuple[Decimal, int]]:
    if not raw:
        return []
    pairs: List[Tuple[Decimal, int]] = []
    for chunk in raw.split(","):
        item = chunk.strip()
        if not item:
            continue
        if ":" in item:
            left, right = item.split(":", 1)
        else:
            match = PAIR_RE.match(item)
            if match:
                left, right = match.group(1), match.group(2)
            else:
                continue
        value = _parse_decimal(left)
        try:
            count = int(right.strip())
        except ValueError:
            continue
        if value is None or count < 0:
            continue
        pairs.append((value, count))
    return pairs


def reconcile_cash_drawer(
    pairs_raw: str | None,
    expected_raw: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    pairs = _parse_pairs(pairs_raw)
    if not pairs:
        return None, "Enter denominations as value:count pairs."

    expected = None
    if expected_raw and expected_raw.strip():
        expected = _parse_decimal(expected_raw)
        if expected is None:
            return None, "Expected total must be a number."

    total = Decimal("0")
    breakdown: List[Dict[str, Any]] = []
    for value, count in pairs:
        line_total = (value * Decimal(count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += line_total
        breakdown.append(
            {
                "denomination": str(value),
                "count": count,
                "line_total": str(line_total),
            }
        )

    total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    diff = None
    if expected is not None:
        diff = (total - expected).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "total": str(total),
        "expected": str(expected) if expected is not None else None,
        "difference": str(diff) if diff is not None else None,
        "breakdown": breakdown,
    }, None
