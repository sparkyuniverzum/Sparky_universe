from __future__ import annotations

from fastapi import status


class DomainError(Exception):
    """Domain-level exception normalized by the global error handler."""

    def __init__(
        self,
        detail: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.code = code


__all__ = ["DomainError"]
