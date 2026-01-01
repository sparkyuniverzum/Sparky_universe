from __future__ import annotations

import os
from pathlib import Path
import secrets
import time
from typing import Any, Dict

from fastapi import Depends, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from universe.registry import load_modules

try:  # Optional if running without DB yet.
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


security = HTTPBasic()

_CACHE_TTL_SECONDS = 5.0
_OVERRIDES_CACHE: Dict[str, Any] = {"ts": 0.0, "data": {}, "source": "memory"}
_IN_MEMORY_OVERRIDES: Dict[str, bool] = {}
_SCHEMA_READY = False


def _admin_user() -> str:
    return os.getenv("SPARKY_ADMIN_USER", "").strip()


def _admin_password() -> str:
    return os.getenv("SPARKY_ADMIN_PASSWORD", "").strip()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    user = _admin_user()
    password = _admin_password()
    if not user or not password:
        raise HTTPException(status_code=503, detail="Admin auth not configured")
    valid_user = secrets.compare_digest(credentials.username, user)
    valid_pass = secrets.compare_digest(credentials.password, password)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


def _dsn() -> str | None:
    return (
        os.getenv("SPARKY_ADMIN_DB_DSN")
        or os.getenv("SPARKY_DB_DSN")
        or os.getenv("DATABASE_URL")
    )


def _db_available() -> bool:
    return bool(_dsn()) and psycopg is not None


def _ensure_schema(conn: Any) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sparky_module_overrides (
            name TEXT PRIMARY KEY,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    _SCHEMA_READY = True


def _fetch_overrides_from_db() -> Dict[str, bool]:
    dsn = _dsn()
    if not dsn or psycopg is None:
        return {}
    with psycopg.connect(dsn, autocommit=True) as conn:
        _ensure_schema(conn)
        rows = conn.execute(
            "SELECT name, enabled FROM sparky_module_overrides"
        ).fetchall()
    return {row[0]: bool(row[1]) for row in rows}


def get_module_overrides() -> Dict[str, bool]:
    now = time.time()
    if now - _OVERRIDES_CACHE["ts"] < _CACHE_TTL_SECONDS:
        return dict(_OVERRIDES_CACHE["data"])
    if _db_available():
        try:
            data = _fetch_overrides_from_db()
            _OVERRIDES_CACHE.update(
                {"ts": now, "data": data, "source": "db"}
            )
            return dict(data)
        except Exception:
            _OVERRIDES_CACHE.update(
                {"ts": now, "data": dict(_IN_MEMORY_OVERRIDES), "source": "memory"}
            )
            return dict(_IN_MEMORY_OVERRIDES)
    _OVERRIDES_CACHE.update(
        {"ts": now, "data": dict(_IN_MEMORY_OVERRIDES), "source": "memory"}
    )
    return dict(_IN_MEMORY_OVERRIDES)


def overrides_source() -> str:
    get_module_overrides()
    return str(_OVERRIDES_CACHE.get("source", "memory"))


def set_module_override(name: str, enabled: bool) -> None:
    name = name.strip()
    if not name:
        return
    if _db_available():
        try:
            dsn = _dsn()
            if not dsn or psycopg is None:
                raise RuntimeError("DB not configured")
            with psycopg.connect(dsn, autocommit=True) as conn:
                _ensure_schema(conn)
                conn.execute(
                    """
                    INSERT INTO sparky_module_overrides (name, enabled, updated_at)
                    VALUES (%s, %s, now())
                    ON CONFLICT (name)
                    DO UPDATE SET enabled = EXCLUDED.enabled, updated_at = now();
                    """,
                    (name, enabled),
                )
        except Exception:
            _IN_MEMORY_OVERRIDES[name] = enabled
    else:
        _IN_MEMORY_OVERRIDES[name] = enabled
    _OVERRIDES_CACHE.update({"ts": 0.0, "data": {}, "source": _OVERRIDES_CACHE["source"]})


def module_enabled(name: str, overrides: Dict[str, bool] | None = None) -> bool:
    if overrides is None:
        overrides = get_module_overrides()
    return overrides.get(name, True)


def get_disabled_modules() -> set[str]:
    overrides = get_module_overrides()
    return {name for name, enabled in overrides.items() if not enabled}


def build_mount_map(modules: Dict[str, Dict[str, Any]] | None = None) -> Dict[str, str]:
    modules = modules or load_modules()
    mount_map: Dict[str, str] = {}
    for meta in modules.values():
        mount = meta.get("mount") or f"/{meta.get('slug', meta.get('name', ''))}"
        if not mount.startswith("/"):
            mount = "/" + mount
        mount_map[mount.rstrip("/")] = meta.get("name", "")
    return mount_map


def resolve_module_name(path: str, root_path: str, mount_map: Dict[str, str]) -> str | None:
    root_path = root_path.rstrip("/")
    if root_path and root_path in mount_map:
        return mount_map[root_path]

    if not path.startswith("/"):
        path = "/" + path
    for mount in sorted(mount_map.keys(), key=len, reverse=True):
        if path == mount or path.startswith(f"{mount}/"):
            return mount_map[mount]
    return None


class DisabledModulesMiddleware:
    def __init__(self, app: Any, mount_map: Dict[str, str]) -> None:
        self.app = app
        self.mount_map = mount_map

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if (
            path == "/"
            or path.startswith("/admin")
            or path.startswith("/category")
            or path.startswith("/docs")
            or path.startswith("/openapi.json")
            or path.startswith("/brand")
            or path.startswith("/favicon")
            or path.startswith("/ads.txt")
        ):
            await self.app(scope, receive, send)
            return

        module = resolve_module_name(path, scope.get("root_path", ""), self.mount_map)
        if module and module in get_disabled_modules():
            response = PlainTextResponse("Module disabled", status_code=404)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
