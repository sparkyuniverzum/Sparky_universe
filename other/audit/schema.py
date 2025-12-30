from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    id: str
    at: datetime
    actor_id: str | None
    method: str
    resource: str
    request_payload: str
    response_status: int | None

    model_config = ConfigDict(from_attributes=True)


__all__ = ["AuditLogOut"]
