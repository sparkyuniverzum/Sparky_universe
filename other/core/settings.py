# backend/app/core/settings.py
from __future__ import annotations

import os
import socket
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv, dotenv_values
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ===== cesty a .env loader ====================================================

BASE_DIR = Path(__file__).resolve().parents[2]


def _load_env() -> None:
    """
    Spolehlivé načtení konfigurace s prioritami:
    1) systémové proměnné (už nastavené v OS) mají nejvyšší prioritu
    2) ENV-<ENV> soubor podle hodnoty ENV (prod/test/dev) přepíše hodnoty ze společného .env
    3) společný .env je základ
    Pokud je nastaveno SKIP_DOTENV, nenačítá nic z diskových souborů.
    """
    if (os.getenv("SKIP_DOTENV") or "").lower() in {"1", "true", "yes"}:
        return
    common_path = BASE_DIR / ".env"
    base_vals = dotenv_values(common_path) if common_path.exists() else {}

    prefer = os.getenv("ENV", base_vals.get("ENV", "dev")).lower()
    env_file = {
        "prod": BASE_DIR / "ENV-PROD",
        "test": BASE_DIR / "ENV-TEST",
    }.get(prefer, BASE_DIR / "ENV-DEV")
    env_vals = dotenv_values(env_file) if env_file.exists() else {}

    # slouč hodnoty: nejdřív společné, pak override z konkrétního env
    merged = {**base_vals, **env_vals}
    # zajistíme ENV pro další načtení
    if "ENV" not in merged:
        merged["ENV"] = prefer

    # zapiš jen ty proměnné, které ještě nejsou v os.environ
    for key, value in merged.items():
        if key in os.environ:
            continue
        if value is None:
            continue
        os.environ[key] = str(value)


def _parse_csv_env(name: str) -> list[str]:
    raw = os.getenv(name, "") or ""
    return [it.strip() for it in raw.split(",") if it.strip()]


# ===== pomocné funkce =========================================================


def _resolvable(host: str) -> bool:
    """Vrátí True pokud DNS umí přeložit host, jinak False (nechceme padat na getaddrinfo)."""
    try:
        socket.getaddrinfo(host, None)
        return True
    except Exception:
        return False


def _normalize_database_url(raw_url: str) -> str:
    """
    - Pokud není nastaveno → použijeme lokální Postgres (localhost:5432, sis_user/sis_pass/db)
    - Pokud je použito schéma postgres://, přepíšeme ho na postgresql:// kvůli SQLAlchemy
    - Async varianta postgresql+asyncpg zůstává beze změny
    """
    raw = (raw_url or "").strip()
    if not raw:
        return "postgresql+asyncpg://sis_user:sis_pass@localhost:5432/db"

    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql://", 1)
    return raw


# ===== Pydantic settings ======================================================


class Settings(BaseSettings):
    AUDIT_ENABLED: bool = False
    model_config = SettingsConfigDict(
        env_file=None,  # .env řešíme ručně přes _load_env()
        extra="ignore",
        populate_by_name=True,
    )

    # obecné
    env: str = Field(default=os.getenv("ENV", "dev"))
    dev_auth_bypass: bool = Field(
        default=os.getenv("DEV_AUTH_BYPASS", "false").lower() == "true"
    )
    auth_disabled: bool = Field(
        default=os.getenv("AUTH_DISABLED", "false").lower() == "true"
    )

    # auth
    api_key: str = Field(
        default=os.getenv("API_KEY", os.getenv("API_KEY_DEV", "dev"))
    )
    api_key_dev: str = Field(default=os.getenv("API_KEY_DEV", "dev"))
    dev_default_actor: str = Field(default=os.getenv("DEV_DEFAULT_ACTOR", "system"))

    # DB
    database_url: str = Field(
        default=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://sis_user:sis_pass@localhost:5432/db",
        )
    )

    # CORS
    cors_origins: str | List[str] = Field(default="*", alias="CORS_ORIGINS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        # treat any string as CSV list
        if isinstance(v, str):
            return [part.strip() for part in v.split(",") if part.strip()]
        return []

    # SMTP (jen sanity log – fallback neřešíme, jen upozorníme při bootu)
    smtp_host: str | None = Field(default=os.getenv("SMTP_HOST"))
    smtp_port: int | None = Field(default=int(os.getenv("SMTP_PORT", "0") or 0))

    # JWT
    JWT_SECRET_KEY: str = Field(default=os.getenv("JWT_SECRET_KEY", "CHANGE_ME"))
    JWT_ALGORITHM: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"))

    # PDF import
    pdf_import_supplier_id: str | None = Field(
        default=os.getenv("PDF_IMPORT_SUPPLIER_ID")
    )

    # Audit retention (days); 0 disables cleanup
    audit_retention_days: int = Field(default=int(os.getenv("AUDIT_RETENTION_DAYS", "180") or 180))


@lru_cache()
def get_settings() -> Settings:
    """
    Public factory používaná všude v aplikaci.
    Postará se o načtení .env a o normalizaci/fallback DATABASE_URL.
    """
    _load_env()

    # načti pydantic Settings (čti ENV)
    s = Settings()

    data = s.model_dump()

    # Prod prostředí: vynucené bezpečnostní volby
    env_name = str(data.get("env") or "").lower()
    if env_name == "prod":
        data["dev_auth_bypass"] = False
        data["auth_disabled"] = False

    # normalizuj/fallback DB URL
    data["database_url"] = _normalize_database_url(data["database_url"])

    # případně zaloguj SMTP DNS problém (jen informace – neblokuje start)
    if data.get("smtp_host") and not _resolvable(data["smtp_host"]):  # type: ignore[arg-type]
        print(
            f"[BOOT] SMTP_HOST '{data['smtp_host']}' není resolvovatelný → e-maily mohou selhat v runtime."
        )

    return Settings(**data)


# convenience instance pro moduly, které chtějí settings hned
settings = get_settings()
