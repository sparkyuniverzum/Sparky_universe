from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP

Q4 = Decimal("0.0001")
Q3 = Decimal("0.001")
Q2 = Decimal("0.01")


def q4(x) -> Decimal:
    """Kvantizace na 4 desetinná místa (např. unit_price v DB NUMERIC(18,4))."""
    d = Decimal(str(x))
    return d.quantize(Q4, rounding=ROUND_HALF_UP)


def q3(x) -> Decimal:
    """Kvantizace na 3 desetinná místa (např. množství)."""
    d = Decimal(str(x))
    return d.quantize(Q3, rounding=ROUND_HALF_UP)


def q2(x) -> Decimal:
    """Kvantizace na 2 desetinná místa (např. vat_rate v DB NUMERIC(5,2))."""
    d = Decimal(str(x))
    return d.quantize(Q2, rounding=ROUND_HALF_UP)


__all__ = ["q2", "q3", "q4"]
