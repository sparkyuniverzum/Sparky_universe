from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.core.dependencies.auth import get_current_user
from app.domains.users.model import User, UserRole
from app.core.settings import get_settings


def _bypass() -> bool:
    s = get_settings()
    return s.env in {"dev", "test"} and bool(getattr(s, "dev_auth_bypass", False))


def require_role(role: str):
    async def _dep(current_user: User = Depends(get_current_user)) -> User:
        if _bypass():
            return current_user
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        if getattr(current_user, "role", None) != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return _dep


require_owner = require_role(UserRole.ADMIN)
require_sales = require_role(UserRole.SALES)
require_warehouse = require_role(UserRole.WAREHOUSE)
require_audit = require_owner
