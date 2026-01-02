from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Iterable, Tuple


_SKIP_PATH_PARTS = {
    "docs",
    "openapi.json",
    "brand",
    "favicon.ico",
    "ads.txt",
    "sitemap.xml",
}


def _parse_int(raw: str | None, default: int | None) -> int | None:
    if raw is None:
        return default
    raw = raw.strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if value <= 0:
        return None
    return value


def _parse_float(raw: str | None, default: float | None) -> float | None:
    if raw is None:
        return default
    raw = raw.strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if value <= 0:
        return None
    return value


def _parse_mapping(raw: str | None) -> Dict[str, int]:
    if not raw:
        return {}
    mapping: Dict[str, int] = {}
    for chunk in raw.split(","):
        if not chunk.strip():
            continue
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        key = key.strip()
        if not key:
            continue
        parsed = _parse_int(value.strip(), None)
        if parsed is not None:
            mapping[key] = parsed
    return mapping


def max_body_bytes() -> int | None:
    default = 5_000_000
    return _parse_int(os.getenv("SPARKY_MAX_BODY_BYTES"), default)


def request_timeout_seconds() -> float | None:
    default = 15.0
    return _parse_float(os.getenv("SPARKY_REQUEST_TIMEOUT_SECONDS"), default)


def module_max_body_overrides() -> Dict[str, int]:
    return _parse_mapping(os.getenv("SPARKY_MODULE_MAX_BODY_BYTES"))


def module_timeout_overrides() -> Dict[str, int]:
    return _parse_mapping(os.getenv("SPARKY_MODULE_TIMEOUTS"))


def _header_value(headers: Iterable[Tuple[bytes, bytes]], key: bytes) -> str | None:
    for header_key, header_value in headers:
        if header_key.lower() == key:
            return header_value.decode("latin-1")
    return None


def _should_skip(path: str, admin_prefix: str) -> bool:
    if path.startswith(admin_prefix):
        return True
    parts = [part for part in path.split("/") if part]
    return any(part in _SKIP_PATH_PARTS for part in parts)


def _resolve_module(path: str, root_path: str, mount_map: Dict[str, str]) -> str | None:
    root_path = root_path.rstrip("/")
    if root_path and root_path in mount_map:
        return mount_map[root_path]

    if not path.startswith("/"):
        path = "/" + path
    for mount in sorted(mount_map.keys(), key=len, reverse=True):
        if path == mount or path.startswith(f"{mount}/"):
            return mount_map[mount]
    return None


async def _send_text(send: Any, status_code: int, message: str) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        }
    )
    await send({"type": "http.response.body", "body": message.encode("utf-8")})


class _RequestTooLarge(Exception):
    pass


class RequestLimitsMiddleware:
    def __init__(
        self,
        app: Any,
        *,
        mount_map: Dict[str, str],
        admin_prefix: str,
        max_body: int | None = None,
        timeout_seconds: float | None = None,
        module_max_body: Dict[str, int] | None = None,
        module_timeouts: Dict[str, int] | None = None,
    ) -> None:
        self.app = app
        self.mount_map = mount_map
        self.admin_prefix = admin_prefix
        self.max_body = max_body
        self.timeout_seconds = timeout_seconds
        self.module_max_body = module_max_body or {}
        self.module_timeouts = module_timeouts or {}

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if _should_skip(path, self.admin_prefix):
            await self.app(scope, receive, send)
            return

        module = _resolve_module(path, scope.get("root_path", ""), self.mount_map) or ""
        max_body = self.module_max_body.get(module, self.max_body)
        timeout_seconds = self.module_timeouts.get(module, self.timeout_seconds)

        if max_body is None and timeout_seconds is None:
            await self.app(scope, receive, send)
            return

        headers = scope.get("headers", [])
        content_length = _header_value(headers, b"content-length")
        if max_body is not None and content_length and content_length.isdigit():
            if int(content_length) > max_body:
                await _send_text(send, 413, "Payload too large")
                return

        response_started = False
        body_bytes = 0

        async def receive_wrapper() -> Dict[str, Any]:
            nonlocal body_bytes
            message = await receive()
            if message.get("type") == "http.request":
                body = message.get("body", b"")
                if body:
                    body_bytes += len(body)
                    if max_body is not None and body_bytes > max_body:
                        raise _RequestTooLarge()
            return message

        async def send_wrapper(message: Dict[str, Any]) -> None:
            nonlocal response_started
            if message.get("type") == "http.response.start":
                response_started = True
            await send(message)

        try:
            if timeout_seconds is not None:
                await asyncio.wait_for(
                    self.app(scope, receive_wrapper, send_wrapper),
                    timeout=timeout_seconds,
                )
            else:
                await self.app(scope, receive_wrapper, send_wrapper)
        except _RequestTooLarge:
            if not response_started:
                await _send_text(send, 413, "Payload too large")
        except asyncio.TimeoutError:
            if not response_started:
                await _send_text(send, 504, "Request timed out")
