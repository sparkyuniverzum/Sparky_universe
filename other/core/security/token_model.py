from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class AccessTokenPayload(BaseModel):
    """Structured payload for an access token"""
    user_id: str
    session_id: str


class TokenPair(BaseModel):
    """Access + Refresh token pair container"""
    access_token: str
    refresh_token: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    session_id: str


class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    role: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None
    last_refresh_at: datetime | None = None

