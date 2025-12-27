from __future__ import annotations

from typing import Protocol

from app.core.security.token_model import TokenPair


class SessionManager(Protocol):
    async def create_session(self, user_id: str, device: str, ip: str, role: str | None = None) -> TokenPair:
        """Create new session"""
        raise NotImplementedError

    async def revoke_session(self, session_id: str) -> None:
        """Revoke session"""
        raise NotImplementedError

    async def validate_refresh_token(self, refresh_token: str) -> dict:
        """Validate refresh token"""
        raise NotImplementedError

    async def rotate_refresh_token(self, session_id: str) -> TokenPair:
        """Rotate refresh token"""
        raise NotImplementedError
