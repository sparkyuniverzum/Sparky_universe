from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import csv
import io

from app.core.dependencies import get_session
from app.domains.ledger.schemas.ledger_entry import LedgerEntryOut
from app.api.schemas.common import ListResponse
from app.domains.ledger.models.model import LedgerEntry
from app.domains.ledger.models.balance import LedgerBalance
from app.api.responses import get_response_factory, ResponseFactory
from app.core.dependencies.permissions import require_owner

router = APIRouter(
    prefix="/ledger",
    tags=["ledger"],
    dependencies=[Depends(require_owner)],
)


@router.get("", response_model=ListResponse[LedgerEntryOut])
async def list_ledger(
    product_id: str | None = Query(None),
    batch_id: str | None = Query(None),
    direction: str | None = Query(None, description="IN/OUT/ADJUST"),
    from_at: str | None = Query(None),
    to_at: str | None = Query(None),
    export: str | None = Query(None, alias="format", description="Set to 'csv' to export"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    if limit <= 0 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be non-negative")

    def _parse_dt(val: str | None):
        from datetime import datetime
        if not val:
            return None
        try:
            return datetime.fromisoformat(val)
        except Exception:
            raise HTTPException(status_code=422, detail="from_at/to_at must be ISO datetime")

    filters = []
    if product_id:
        filters.append(LedgerEntry.product_id == product_id)
    if batch_id:
        filters.append(LedgerEntry.batch_id == batch_id)
    if direction:
        filters.append(LedgerEntry.reason == direction)
    from_dt = _parse_dt(from_at)
    to_dt = _parse_dt(to_at)
    if from_dt:
        filters.append(LedgerEntry.created_at >= from_dt)
    if to_dt:
        filters.append(LedgerEntry.created_at <= to_dt)

    stmt = select(LedgerEntry).order_by(LedgerEntry.created_at.desc())
    if filters:
        stmt = stmt.where(and_(*filters))
    count_stmt = select(func.count()).select_from(stmt.subquery())

    rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()

    if export == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "product_id",
                "batch_id",
                "movement_id",
                "quantity",
                "balance_after",
                "reason",
                "reference_id",
                "warehouse_id",
                "doc_type",
                "doc_id",
                "created_at",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.id,
                    r.product_id,
                    r.batch_id,
                    r.movement_id,
                    r.quantity,
                    r.balance_after,
                    r.reason,
                    r.reference_id,
                    getattr(r, "warehouse_id", None),
                    getattr(r, "doc_type", None),
                    getattr(r, "doc_id", None),
                    r.created_at.isoformat() if r.created_at else "",
                ]
            )
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv")

    payload = {
        "data": [LedgerEntryOut.model_validate(r).model_dump(mode="json") for r in rows],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }
    return responses.list(payload)


@router.get("/balances")
async def list_balances(
    product_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    stmt = select(LedgerBalance).order_by(LedgerBalance.updated_at.desc())
    if product_id:
        stmt = stmt.where(LedgerBalance.product_id == product_id)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    data = [
        {
            "product_id": r.product_id,
            "balance": str(r.balance),
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]
    return responses.list({"data": data, "meta": {"total": total, "limit": limit, "offset": offset}})


@router.get("/balances/batches")
async def list_batch_balances(
    product_id: str | None = None,
    batch_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
):
    stmt = (
        select(
            LedgerEntry.batch_id,
            LedgerEntry.product_id,
            func.coalesce(func.sum(LedgerEntry.quantity), 0).label("balance"),
            func.max(LedgerEntry.created_at).label("updated_at"),
        )
        .group_by(LedgerEntry.batch_id, LedgerEntry.product_id)
        .order_by(func.max(LedgerEntry.created_at).desc())
    )
    if product_id:
        stmt = stmt.where(LedgerEntry.product_id == product_id)
    if batch_id:
        stmt = stmt.where(LedgerEntry.batch_id == batch_id)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    rows = (await db.execute(stmt.limit(limit).offset(offset))).all()
    total = (await db.execute(count_stmt)).scalar_one()
    data = [
        {
            "batch_id": row.batch_id,
            "product_id": row.product_id,
            "balance": str(row.balance),
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
        for row in rows
        if row.batch_id
    ]
    return responses.list({"data": data, "meta": {"total": total, "limit": limit, "offset": offset}})


__all__ = ["router"]
