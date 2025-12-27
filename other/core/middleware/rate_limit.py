from __future__ import annotations

import time
from collections import defaultdict
from typing import Awaitable, Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.core.settings import get_settings


class _RateLimiter:
    def __init__(self) -> None:
        self.bucket: dict[str, list[float]] = defaultdict(list)

    def hit(self, key: str, limit: int, window: float) -> bool:
        """Return True if allowed, False if over limit."""
        now = time.monotonic()
        window_start = now - window
        buf = self.bucket[key]
        # drop old timestamps
        while buf and buf[0] < window_start:
            buf.pop(0)
        if len(buf) >= limit:
            return False
        buf.append(now)
        return True


rate_limiter = _RateLimiter()


def _bypass() -> bool:
    s = get_settings()
    return s.env in {"dev", "test"} and bool(getattr(s, "dev_auth_bypass", False))


def _client_ip(request: Request) -> str:
    if request.client:
        return request.client.host or "unknown"
    return request.headers.get("x-forwarded-for", "unknown").split(",")[0].strip() or "unknown"


async def rate_limit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if _bypass():
        return await call_next(request)

    ip = _client_ip(request)
    path = request.url.path
    method = request.method.upper()

    # Specific limits per endpoint (path + method)
    specific_limits: dict[tuple[str, str], tuple[int, float]] = {
        ("/v1/auth/login", "POST"): (5, 60.0),
        ("/v1/auth/refresh", "POST"): (20, 60.0),
        ("/v1/auth/register", "POST"): (3, 60.0),
    }

    # Check specific limit first
    specific = specific_limits.get((path, method))
    if specific:
        limit, window = specific
        key = f"{ip}:{path}"
        if not rate_limiter.hit(key, limit, window):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please slow down."},
            )

    # Global limit per IP (rolling window 60s)
    global_limit, global_window = 100, 60.0
    global_key = f"{ip}:__global__"
    if not rate_limiter.hit(global_key, global_limit, global_window):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please slow down."},
        )

    return await call_next(request)
