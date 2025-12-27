# backend/app/core/mapping.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Callable, Dict, Tuple, Type, TypeVar

from app.core.utils.conversions import dec_to_str, str_to_dec

# proč: centrální registry pro všechny mapy (1 místo pravdy)
T = TypeVar("T")


@dataclass(frozen=True)
class _Key:
    src: Type[Any]
    dst: Type[Any]


class _MapperRegistry:
    def __init__(self) -> None:
        self._fns: Dict[_Key, Callable[[Any, Type[Any], Dict[str, Any]], Any]] = {}

    # proč: explicitní registr map – snadno dohledatelné a testovatelné
    def register(
        self, src: Type[Any], dst: Type[Any]
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def deco(
            fn: Callable[[Any, Type[Any], Dict[str, Any]], Any],
        ) -> Callable[[Any, Type[Any], Dict[str, Any]], Any]:
            self._fns[_Key(src, dst)] = fn
            return fn

        return deco

    def map(self, obj: Any, dst: Type[T], ctx: Dict[str, Any] | None = None) -> T:
        if obj is None:
            return None  # type: ignore[return-value]
        ctx = ctx or {}
        key = _Key(type(obj), dst)
        fn = self._fns.get(key)
        if not fn:
            raise KeyError(
                f"No mapping registered for {type(obj).__name__} -> {dst.__name__}"
            )
        return fn(obj, dst, ctx)  # type: ignore[return-value]


# singleton
mapper = _MapperRegistry()


def dt_to_iso(v: datetime | date | None) -> str | None:
    """Proč: API vrací ISO8601 stringy, ORM má datetime/date."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.replace(microsecond=0).isoformat() + "Z"
    return datetime(v.year, v.month, v.day).isoformat() + "Z"
