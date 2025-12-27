from __future__ import annotations

from typing import Any

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError


class BaseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add_and_refresh(self, model: Any) -> Any:
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return model

    async def scalars(self, stmt) -> list[Any]:
        return list((await self.db.execute(stmt)).scalars().all())

    async def scalar(self, stmt) -> Any:
        return (await self.db.execute(stmt)).scalar()

    async def scalar_one(self, stmt) -> Any:
        return (await self.db.execute(stmt)).scalar_one()

    async def get_or_fail(
        self,
        model,
        obj_id: Any,
        *,
        detail: str | None = None,
        code: str | None = None,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ) -> Any:
        obj = await self.db.get(model, obj_id)
        if not obj:
            raise DomainError(
                detail or f"{model.__name__} not found",
                code=code or f"{model.__tablename__}_not_found",
                status_code=status_code,
            )
        return obj


__all__ = ["BaseRepository"]
