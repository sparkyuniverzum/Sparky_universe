from __future__ import annotations

from typing import Protocol

from argon2 import PasswordHasher as Argon2Lib
from argon2.exceptions import VerifyMismatchError


class PasswordHasher(Protocol):
    async def hash(self, password: str) -> str:
        """Return hashed password"""
        raise NotImplementedError

    async def verify(self, password: str, hashed: str) -> bool:
        """Verify password"""
        raise NotImplementedError


class Argon2Hasher:
    """Async-friendly wrapper nad argon2-cffi."""

    def __init__(self) -> None:
        self._hasher = Argon2Lib()

    async def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    async def verify(self, password: str, hashed: str) -> bool:
        try:
            return self._hasher.verify(hashed, password)
        except VerifyMismatchError:
            return False
