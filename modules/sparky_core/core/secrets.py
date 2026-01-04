from __future__ import annotations

import logging
import os


logger = logging.getLogger(__name__)


def require_secret(
    env_name: str,
    *,
    allow_insecure_env: str | None = "SPARKY_ALLOW_INSECURE_SECRETS",
    insecure_default: str = "dev-secret",
) -> str:
    value = os.getenv(env_name, "").strip()
    if value:
        return value
    allow_insecure = False
    if allow_insecure_env:
        raw = os.getenv(allow_insecure_env, "").strip().lower()
        allow_insecure = raw in {"1", "true", "yes", "on"}
    if allow_insecure:
        logger.warning(
            "%s not set; using insecure default because %s is enabled.",
            env_name,
            allow_insecure_env,
        )
        return insecure_default
    raise RuntimeError(
        f"{env_name} is required; set it or enable {allow_insecure_env}=on for local dev."
    )
