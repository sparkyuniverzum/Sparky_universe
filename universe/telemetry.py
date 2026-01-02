from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from http.cookies import SimpleCookie
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import parse_qs, urlparse

from universe.registry import load_modules

logger = logging.getLogger(__name__)

SESSION_COOKIE = "sparky_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 365

SKIP_PATH_PARTS = {
    "docs",
    "openapi.json",
    "brand",
    "favicon.ico",
}


def _flag(name: str, default: str = "off") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def telemetry_enabled() -> bool:
    return _flag("SPARKY_TELEMETRY", "off")


def _auto_migrate() -> bool:
    return _flag("SPARKY_TELEMETRY_AUTO_MIGRATE", "on")


def _dsn() -> str | None:
    return os.getenv("SPARKY_DB_DSN") or os.getenv("DATABASE_URL")


def _telemetry_salt() -> str:
    return os.getenv("SPARKY_TELEMETRY_SALT", "")


def _hash_value(value: str | None) -> str | None:
    if not value:
        return None
    raw = f"{_telemetry_salt()}{value}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _build_module_map() -> Dict[str, str]:
    modules = load_modules()
    mount_map: Dict[str, str] = {}
    for meta in modules.values():
        mount = meta.get("mount") or f"/{meta.get('slug', meta['name'])}"
        if not mount.startswith("/"):
            mount = "/" + mount
        mount_map[mount.rstrip("/")] = meta["name"]
    return mount_map


def _resolve_module(path: str, root_path: str, mount_map: Dict[str, str]) -> str:
    root_path = root_path.rstrip("/")
    if root_path and root_path in mount_map:
        return mount_map[root_path]

    if not path.startswith("/"):
        path = "/" + path
    for mount in sorted(mount_map.keys(), key=len, reverse=True):
        if path == mount or path.startswith(f"{mount}/"):
            return mount_map[mount]
    return "universe"


def _should_skip(path: str) -> bool:
    parts = [part for part in path.split("/") if part]
    return any(part in SKIP_PATH_PARTS for part in parts)


def _header_value(headers: Iterable[Tuple[bytes, bytes]], key: bytes) -> str | None:
    for header_key, header_value in headers:
        if header_key.lower() == key:
            return header_value.decode("latin-1")
    return None


def _get_cookie(headers: Iterable[Tuple[bytes, bytes]], name: str) -> str | None:
    raw = _header_value(headers, b"cookie")
    if not raw:
        return None
    cookie = SimpleCookie()
    cookie.load(raw)
    if name in cookie:
        return cookie[name].value
    return None


def _set_cookie_header(value: str, secure: bool) -> bytes:
    cookie = SimpleCookie()
    cookie[SESSION_COOKIE] = value
    cookie[SESSION_COOKIE]["path"] = "/"
    cookie[SESSION_COOKIE]["max-age"] = str(SESSION_TTL_SECONDS)
    cookie[SESSION_COOKIE]["httponly"] = True
    cookie[SESSION_COOKIE]["samesite"] = "Lax"
    if secure:
        cookie[SESSION_COOKIE]["secure"] = True
    return cookie.output(header="").strip().encode("latin-1")


def _request_id(headers: Iterable[Tuple[bytes, bytes]]) -> str:
    existing = _header_value(headers, b"x-request-id")
    return existing or str(uuid.uuid4())


def _client_ip(headers: Iterable[Tuple[bytes, bytes]], client: Any) -> str | None:
    if _flag("SPARKY_TRUST_PROXY", "off"):
        forwarded = _header_value(headers, b"x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    if client and getattr(client, "host", None):
        return client.host
    return None


def _extract_utm(query_string: bytes) -> Dict[str, str]:
    if not query_string:
        return {}
    try:
        parsed = parse_qs(query_string.decode("utf-8", errors="ignore"))
    except Exception:
        return {}
    keys = {
        "utm_source": "utm_source",
        "utm_medium": "utm_medium",
        "utm_campaign": "utm_campaign",
        "utm_term": "utm_term",
        "utm_content": "utm_content",
    }
    result: Dict[str, str] = {}
    for key, out_key in keys.items():
        values = parsed.get(key)
        if values:
            value = values[0].strip()
            if value:
                result[out_key] = value
    return result


def _referrer_host(referrer: str | None) -> str | None:
    if not referrer:
        return None
    try:
        return urlparse(referrer).netloc or None
    except Exception:
        return None


class TelemetryClient:
    def __init__(self, dsn: str, *, auto_migrate: bool = True) -> None:
        try:
            import psycopg
            from psycopg_pool import ConnectionPool
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("psycopg is required for telemetry.") from exc

        self._dsn = dsn
        self._pool = ConnectionPool(
            dsn,
            min_size=1,
            max_size=5,
            kwargs={"autocommit": True},
        )
        if auto_migrate:
            self._ensure_schema()

    def _ensure_schema(self) -> None:
        queries = [
            """
            CREATE TABLE IF NOT EXISTS telemetry_events (
                id UUID PRIMARY KEY,
                ts TIMESTAMPTZ NOT NULL DEFAULT now(),
                tenant TEXT,
                module TEXT,
                path TEXT,
                method TEXT,
                status INTEGER,
                duration_ms INTEGER,
                event_type TEXT,
                outcome TEXT,
                request_id TEXT,
                session_id TEXT,
                referrer TEXT,
                ua_hash TEXT,
                ip_hash TEXT,
                payload JSONB
            );
            """,
            "CREATE INDEX IF NOT EXISTS telemetry_events_ts_idx ON telemetry_events (ts);",
            "CREATE INDEX IF NOT EXISTS telemetry_events_module_idx ON telemetry_events (module);",
            "CREATE INDEX IF NOT EXISTS telemetry_events_event_idx ON telemetry_events (event_type);",
            "CREATE INDEX IF NOT EXISTS telemetry_events_tenant_idx ON telemetry_events (tenant);",
        ]
        with self._pool.connection() as conn:
            for query in queries:
                conn.execute(query)

    def capture(self, event: Dict[str, Any]) -> None:
        payload = json.dumps(event.get("payload") or {})
        query = """
        INSERT INTO telemetry_events (
            id, ts, tenant, module, path, method, status, duration_ms,
            event_type, outcome, request_id, session_id, referrer,
            ua_hash, ip_hash, payload
        ) VALUES (
            %(id)s, now(), %(tenant)s, %(module)s, %(path)s, %(method)s, %(status)s,
            %(duration_ms)s, %(event_type)s, %(outcome)s, %(request_id)s,
            %(session_id)s, %(referrer)s, %(ua_hash)s, %(ip_hash)s, %(payload)s
        );
        """
        data = {
            **event,
            "payload": payload,
        }
        with self._pool.connection() as conn:
            conn.execute(query, data)


class TelemetryMiddleware:
    def __init__(self, app: Any, client: TelemetryClient, mount_map: Dict[str, str]) -> None:
        self.app = app
        self.client = client
        self.mount_map = mount_map

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "").upper()
        if method in {"HEAD", "OPTIONS"} or _should_skip(path):
            await self.app(scope, receive, send)
            return

        headers = scope.get("headers", [])
        start = time.perf_counter()
        request_id = _request_id(headers)
        session_id = _get_cookie(headers, SESSION_COOKIE)
        new_session = session_id is None
        if new_session:
            session_id = str(uuid.uuid4())

        status_code = 500
        response_headers: List[Tuple[bytes, bytes]] = []
        request_body_bytes = 0
        response_body_bytes = 0

        async def receive_wrapper() -> Dict[str, Any]:
            nonlocal request_body_bytes
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if body:
                    request_body_bytes += len(body)
            return message

        async def send_wrapper(message: Dict[str, Any]) -> None:
            nonlocal status_code, response_headers, response_body_bytes
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                response_headers = list(message.get("headers", []))
                if new_session:
                    secure = scope.get("scheme") == "https"
                    response_headers.append(
                        (b"set-cookie", _set_cookie_header(session_id, secure))
                    )
                if not _header_value(response_headers, b"x-request-id"):
                    response_headers.append((b"x-request-id", request_id.encode("latin-1")))
                message["headers"] = response_headers
            if message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    response_body_bytes += len(body)
            await send(message)

        await self.app(scope, receive_wrapper, send_wrapper)

        duration_ms = int((time.perf_counter() - start) * 1000)
        root_path = scope.get("root_path", "")
        module = _resolve_module(path, root_path, self.mount_map)
        tenant = os.getenv("SPARKY_TENANT") or _header_value(headers, b"host")
        referrer = _header_value(headers, b"referer")
        ua_hash = _hash_value(_header_value(headers, b"user-agent"))
        ip_hash = _hash_value(_client_ip(headers, scope.get("client")))
        query_bytes = scope.get("query_string") or b""
        utm = _extract_utm(query_bytes)
        referrer_host = _referrer_host(referrer)

        event_type = "page_view" if method == "GET" else "action_submit"
        outcome = "success" if status_code < 400 else "error"
        if status_code == 404:
            outcome = "not_found"
        elif method in {"POST", "PUT", "PATCH"} and 400 <= status_code < 500:
            outcome = "validation_error"
        elif 400 <= status_code < 500:
            outcome = "client_error"

        content_length = _header_value(headers, b"content-length")
        request_bytes = request_body_bytes
        if not request_bytes and content_length and content_length.isdigit():
            request_bytes = int(content_length)
        payload = {
            "content_length": int(content_length) if content_length and content_length.isdigit() else None,
            "query_length": len(query_bytes),
            "request_bytes": request_bytes or None,
            "response_bytes": response_body_bytes or None,
            "referrer_host": referrer_host,
            **utm,
        }

        event = {
            "id": str(uuid.uuid4()),
            "tenant": tenant,
            "module": module,
            "path": path,
            "method": method,
            "status": status_code,
            "duration_ms": duration_ms,
            "event_type": event_type,
            "outcome": outcome,
            "request_id": request_id,
            "session_id": session_id,
            "referrer": referrer,
            "ua_hash": ua_hash,
            "ip_hash": ip_hash,
            "payload": payload,
        }

        asyncio.create_task(self._capture(event))

    async def _capture(self, event: Dict[str, Any]) -> None:
        try:
            await asyncio.to_thread(self.client.capture, event)
        except Exception:
            logger.exception("Failed to capture telemetry event.")


def attach_telemetry(app: Any) -> None:
    if not telemetry_enabled():
        return

    dsn = _dsn()
    if not dsn:
        logger.warning("Telemetry enabled but no DB DSN configured.")
        return

    try:
        client = TelemetryClient(dsn, auto_migrate=_auto_migrate())
    except Exception:
        logger.exception("Telemetry initialization failed.")
        return

    mount_map = _build_module_map()
    app.add_middleware(TelemetryMiddleware, client=client, mount_map=mount_map)
