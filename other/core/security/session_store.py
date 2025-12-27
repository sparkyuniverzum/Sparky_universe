from __future__ import annotations

from typing import Protocol

from app.core.security.token_model import SessionInfo, TokenPair


class SessionStore(Protocol):
    """Abstraktní úložiště pro session + refresh tokeny."""

    async def create_session(self, user_id: str, device: str, ip: str, role: str | None = None) -> SessionInfo:
        raise NotImplementedError

    async def revoke_session(self, session_id: str) -> None:
        raise NotImplementedError

    async def get_session(self, session_id: str) -> SessionInfo | None:
        raise NotImplementedError

    async def issue_tokens(self, session: SessionInfo) -> TokenPair:
        """Vygeneruj TokenPair pro danou session."""
        raise NotImplementedError

    async def rotate_refresh_token(self, refresh_token: str) -> TokenPair:
        """Validuj a otoč refresh token, vrať novou dvojici."""
        raise NotImplementedError

    async def touch_session(self, session_id: str) -> None:
        """Aktualizuj updated_at pro IDLE timeout."""
        raise NotImplementedError
