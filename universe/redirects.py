from __future__ import annotations

import os
from typing import Any, Dict, Iterable, Tuple
from urllib.parse import urlsplit


def _header_value(headers: Iterable[Tuple[bytes, bytes]], key: bytes) -> str | None:
    for header_key, header_value in headers:
        if header_key.lower() == key:
            return header_value.decode("latin-1")
    return None


def _flag(name: str, default: str = "off") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _split_host_value(raw: str) -> tuple[str, str]:
    if not raw:
        return "", ""
    raw = raw.strip()
    if not raw:
        return "", ""
    try:
        parts = urlsplit(raw)
    except Exception:
        return raw.lower(), ""
    host = parts.hostname or ""
    port = str(parts.port) if parts.port else ""
    return host.lower(), port


def _split_host_header(raw: str) -> tuple[str, str]:
    if not raw:
        return "", ""
    raw = raw.strip()
    if not raw:
        return "", ""
    try:
        parts = urlsplit(f"//{raw}")
    except Exception:
        return raw.lower(), ""
    host = parts.hostname or ""
    port = str(parts.port) if parts.port else ""
    return host.lower(), port


def _canonical_host() -> tuple[str, str]:
    raw = os.getenv("SPARKY_CANONICAL_HOST") or os.getenv("SPARKY_TENANT") or ""
    if not raw:
        return "", ""
    if "://" not in raw:
        raw = f"https://{raw}"
    return _split_host_value(raw)


def _request_scheme(headers: Iterable[Tuple[bytes, bytes]], scope: Dict[str, Any]) -> str:
    scheme = str(scope.get("scheme") or "http")
    if _flag("SPARKY_TRUST_PROXY", "off"):
        forwarded = _header_value(headers, b"x-forwarded-proto")
        if forwarded:
            scheme = forwarded.split(",")[0].strip()
    return scheme


class WwwRedirectMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app
        self._canonical_host, self._canonical_port = _canonical_host()

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = scope.get("headers", [])
        host_header = _header_value(headers, b"host") or ""
        host, port = _split_host_header(host_header)
        if not host.startswith("www."):
            await self.app(scope, receive, send)
            return

        host_without = host[4:]
        if self._canonical_host and host_without != self._canonical_host:
            await self.app(scope, receive, send)
            return

        target_host = self._canonical_host or host_without
        target_port = self._canonical_port or port
        if not target_host:
            await self.app(scope, receive, send)
            return

        scheme = _request_scheme(headers, scope)
        root_path = scope.get("root_path") or ""
        path = scope.get("path") or ""
        if not path.startswith("/"):
            path = "/" + path
        if root_path and root_path != "/":
            path = root_path.rstrip("/") + path
        if not path:
            path = "/"
        query = scope.get("query_string", b"")
        location = f"{scheme}://{target_host}"
        if target_port:
            location = f"{location}:{target_port}"
        location = f"{location}{path}"
        if query:
            location = f"{location}?{query.decode('latin-1')}"

        await send(
            {
                "type": "http.response.start",
                "status": 308,
                "headers": [(b"location", location.encode("utf-8"))],
            }
        )
        await send({"type": "http.response.body", "body": b""})
