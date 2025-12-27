from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol

from jose import jwt, JWTError

from app.core.settings import get_settings


class JWTManager(Protocol):
    async def create_access_token(self, payload: dict, expires_delta: timedelta | None = None) -> str:
        """Generate access token"""
        raise NotImplementedError

    async def decode_access_token(self, token: str) -> dict:
        """Decode and validate access token"""
        raise NotImplementedError


class JWTManagerImpl:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def create_access_token(self, payload: dict, expires_delta: timedelta | None = None) -> str:
        data = payload.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
        data.update({"exp": expire})
        return jwt.encode(
            data,
            self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM,
        )

    async def decode_access_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                self.settings.JWT_SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM],
            )
        except JWTError as exc:  # pragma: no cover - runtime validation
            raise ValueError("Invalid token") from exc
