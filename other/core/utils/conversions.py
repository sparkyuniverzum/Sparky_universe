from __future__ import annotations
from typing import Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime, date


def iso_to_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return str(v)


def _str_to_dec(v: Any) -> Decimal:
    if v is None:
        return Decimal("0")
    if isinstance(v, Decimal):
        return v
    s = str(v).strip().replace(",", ".")
    if s == "":
        return Decimal("0")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def str_to_dec(v: Any) -> Decimal:
    return _str_to_dec(v)


def dec_to_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    try:
        d = _str_to_dec(v)
        return format(d, "f")
    except Exception:
        return None


def req_str(v: Any, *, field: str = "value") -> str:
    if v is None or str(v).strip() == "":
        raise ValueError(f"{field} is required")
    return str(v)


def money_out(v: Any) -> str:
    d = _str_to_dec(v)
    return format(d, "f")


__all__ = ["iso_to_str", "str_to_dec", "dec_to_str", "req_str", "money_out"]
