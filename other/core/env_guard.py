# app/core/env_guard.py
from __future__ import annotations

from app.core.settings import Settings


class EnvMisconfigured(RuntimeError):
    pass


def validate_environment(s: Settings) -> None:
    """
    Ověří klíčové bezpečné volby podle prostředí.
    - povolené hodnoty env
    - vyžadované klíče a vypnutí bypassu v prod
    """
    allowed_envs = {"dev", "test", "prod"}
    if (s.env or "").lower() not in allowed_envs:
        raise EnvMisconfigured(f"ENV musí být jedna z {sorted(allowed_envs)}, aktuálně '{s.env}'")

    if not s.database_url:
        raise EnvMisconfigured("DATABASE_URL nesmí být prázdné")
    if not s.database_url.startswith("postgresql"):
        raise EnvMisconfigured("DATABASE_URL musí používat PostgreSQL (postgresql+asyncpg://)")

    # Prod guardy
    if s.env == "prod":
        if s.auth_disabled:
            raise EnvMisconfigured("AUTH_DISABLED nesmí být true v prod")
        if s.dev_auth_bypass:
            raise EnvMisconfigured("DEV_AUTH_BYPASS nesmí být true v prod")
        if not s.JWT_SECRET_KEY or s.JWT_SECRET_KEY in {"CHANGE_ME", "dev", "test"} or len(s.JWT_SECRET_KEY) < 32:
            raise EnvMisconfigured("JWT_SECRET_KEY musí být nastavený na silnou hodnotu (min 32 znaků) v prod")
        if s.api_key in {None, "", "dev"}:
            raise EnvMisconfigured("API_KEY musí být nastavený na nefallback hodnotu v prod")
        if getattr(s, "cors_origins", None) in (["*"], ["* "], []):
            raise EnvMisconfigured("CORS_ORIGINS nesmí být '*' v prod – nastav konkrétní origin")

    # Dev/test warning-only checks – případné rozšíření
