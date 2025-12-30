from __future__ import annotations

from typing import Optional, Tuple, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.repository import BaseRepository
from app.domains.inventory.models.receipt import Receipt, ReceiptItem
from app.domains.inventory.schemas.receipt import ReceiptCreate


class ReceiptCRUD(BaseRepository):
    async def create(self, payload: ReceiptCreate) -> Receipt:
        obj = Receipt(
            supplier_id=payload.supplier_id,
            note=payload.note,
        )
        self.db.add(obj)
        await self.db.flush()

        for item in payload.items:
            ri = ReceiptItem(
                receipt_id=obj.id,
                product_id=item.product_id,
                supplier_sku=item.supplier_sku,
                product_name=item.product_name,
                qty=item.qty,
                unit_price=item.unit_price,
                vat_rate=item.vat_rate,
                note=item.note,
                category_id=item.category_id,
                category=item.category,
            )
            self.db.add(ri)
        return obj

    async def get(self, receipt_id: str) -> Receipt:
        return await self.db.get(Receipt, receipt_id)

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        supplier_id: Optional[str],
        q: Optional[str],
    ) -> Tuple[List[Receipt], int]:
        stmt = select(Receipt).order_by(Receipt.created_at.desc())
        count_stmt = select(func.count()).select_from(Receipt)

        if supplier_id:
            stmt = stmt.where(Receipt.supplier_id == supplier_id)
            count_stmt = count_stmt.where(Receipt.supplier_id == supplier_id)

        if q:
            like = f"%{q}%"
            stmt = stmt.where(Receipt.note.ilike(like))
            count_stmt = count_stmt.where(Receipt.note.ilike(like))

        rows = (await self.db.execute(stmt.limit(limit).offset(offset))).scalars().all()
        total = await self.db.scalar(count_stmt)
        return list(rows), int(total or 0)


__all__ = ["ReceiptCRUD"]
