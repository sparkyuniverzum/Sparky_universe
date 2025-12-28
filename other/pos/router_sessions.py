from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_session
from app.core.dependencies.permissions import require_sales
from app.api.responses import get_response_factory, ResponseFactory
from app.api.schemas.common import DetailResponse
from app.domains.pos.service import open_session, close_session, record_cash_transaction
from app.domains.pos.models.cash_drawer_session import CashDrawerSession
from app.domains.pos.models.cash_transaction import CashTransaction

router = APIRouter(
    prefix="/cash-sessions",
    tags=["cash_sessions"],
    dependencies=[Depends(require_sales)],
)


@router.post(
    "/open",
    response_model=DetailResponse[dict],
    status_code=status.HTTP_201_CREATED,
)
async def open_cash_session(
    register_code: str,
    opening_float: Decimal = Decimal("0.00"),
    cashier_id: str | None = None,
    note: str | None = None,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    session = await open_session(db, register_code=register_code, opening_float=opening_float, cashier_id=cashier_id, note=note)
    await db.commit()
    return responses.detail({"data": {"id": session.id, "register_id": session.register_id, "status": session.status}}, status_code=status.HTTP_201_CREATED)


@router.post(
    "/{session_id}/close",
    response_model=DetailResponse[dict],
)
async def close_cash_session(
    session_id: str,
    closing_float: Decimal | None = None,
    note: str | None = None,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    session = await close_session(db, session_id, closing_float=closing_float, note=note)
    await db.commit()
    return responses.detail({"data": {"id": session.id, "status": session.status}}, status_code=status.HTTP_200_OK)


@router.post(
    "/{session_id}/pay-in",
    response_model=DetailResponse[dict],
    status_code=status.HTTP_201_CREATED,
)
async def pay_in(
    session_id: str,
    amount: Decimal,
    reason: str | None = None,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    tx = await record_cash_transaction(db, session_id, tx_type="pay_in", amount=amount, reason=reason)
    await db.commit()
    return responses.detail({"data": {"id": tx.id, "type": tx.type, "amount": str(tx.amount)}}, status_code=status.HTTP_201_CREATED)


@router.post(
    "/{session_id}/pay-out",
    response_model=DetailResponse[dict],
    status_code=status.HTTP_201_CREATED,
)
async def pay_out(
    session_id: str,
    amount: Decimal,
    reason: str | None = None,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    tx = await record_cash_transaction(db, session_id, tx_type="pay_out", amount=amount, reason=reason)
    await db.commit()
    return responses.detail({"data": {"id": tx.id, "type": tx.type, "amount": str(tx.amount)}}, status_code=status.HTTP_201_CREATED)


__all__ = ["router"]
