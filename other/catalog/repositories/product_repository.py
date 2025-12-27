from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Iterable, Optional, Tuple, List

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.repository import BaseRepository
from app.domains.catalog.models.product import Product
from app.domains.catalog.repositories.category_repository import ProductCategoryRepository
from app.domains.catalog.schemas.product import Product as ProductSchema


class ProductRepository(BaseRepository):
    async def list(
        self,
        *,
        q: Optional[str],
        limit: int,
        offset: int,
        only_active: Optional[bool],
    ) -> Tuple[List[Product], int]:
        stmt = select(Product)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(Product.name.ilike(like), Product.barcode.ilike(like)))
        if only_active is not None:
            stmt = stmt.where(Product.is_active.is_(only_active))

        total = await self.scalar_one(select(func.count()).select_from(stmt.subquery()))
        stmt = stmt.order_by(Product.created_at.desc()).limit(limit).offset(offset)
        rows = await self.scalars(stmt)
        return rows, int(total or 0)

    async def get_by_id_or_public(self, identifier: str) -> Optional[Product]:
        res = await self.db.execute(select(Product).where(Product.public_id == identifier))
        row = res.scalars().first()
        if row:
            return row
        res = await self.db.execute(select(Product).where(Product.id == identifier))
        return res.scalars().first()

    async def get_by_public_id(self, public_id: str) -> Optional[Product]:
        return (await self.db.execute(select(Product).where(Product.public_id == public_id))).scalars().first()

    async def get_by_barcode(self, barcode: str) -> Optional[Product]:
        return (await self.db.execute(select(Product).where(Product.barcode == barcode))).scalars().first()

    async def get_by_supplier_sku(self, supplier_id: str | None, supplier_sku: str) -> Optional[Product]:
        if not supplier_sku:
            return None
        stmt = select(Product).where(Product.supplier_sku == supplier_sku)
        return (await self.db.execute(stmt)).scalars().first()

    async def create(self, data: dict) -> Product:
        row = Product(
            id=data.get("id") or str(uuid.uuid4()),
            public_id=data["public_id"],
            name=data["name"],
            unit=data.get("unit", "ks"),
            unit_price=Decimal(str(data.get("unit_price", "0"))),
            vat_rate=Decimal(str(data.get("vat_rate", "21"))),
            reorder_point=Decimal(str(data.get("reorder_point", "0"))),
            reorder_qty=Decimal(str(data.get("reorder_qty", "0"))),
            sku=data.get("sku"),
            barcode=data.get("barcode"),
            supplier_id=data.get("supplier_id"),
            supplier_sku=data.get("supplier_sku"),
            category_id=data.get("category_id"),
            is_active=bool(data.get("is_active", True)),
        )
        return await self.add_and_refresh(row)

    async def update(self, row: Product, data: dict) -> Product:
        if "name" in data and data["name"] is not None:
            row.name = data["name"]
        if "unit" in data and data["unit"] is not None:
            row.unit = data["unit"]
        if "barcode" in data:
            row.barcode = data["barcode"]
        if "sku" in data:
            row.sku = data["sku"]
        if "supplier_id" in data:
            row.supplier_id = data["supplier_id"]
        if "supplier_sku" in data:
            row.supplier_sku = data["supplier_sku"]
        if "category_id" in data:
            row.category_id = data["category_id"]
        if "category_code" in data:
            row.category_code = data["category_code"]
        if "is_active" in data:
            row.is_active = bool(data["is_active"])
        if "unit_price" in data and data["unit_price"] is not None:
            row.unit_price = Decimal(str(data["unit_price"]))
        if "vat_rate" in data and data["vat_rate"] is not None:
            row.vat_rate = Decimal(str(data["vat_rate"]))
        if "reorder_point" in data and data["reorder_point"] is not None:
            row.reorder_point = Decimal(str(data["reorder_point"]))
        if "reorder_qty" in data and data["reorder_qty"] is not None:
            row.reorder_qty = Decimal(str(data["reorder_qty"]))

        try:
            row.version = (row.version or 1) + 1  # type: ignore[attr-defined]
        except Exception:
            pass

        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def deactivate(self, row: Product) -> None:
        row.is_active = False
        try:
            row.version = (row.version or 1) + 1  # type: ignore[attr-defined]
        except Exception:
            pass
        await self.db.flush()

    async def find_matching_by_attributes(
        self,
        *,
        supplier_id: str | None,
        name: str | None,
        unit: str | None,
        unit_price: Decimal,
        vat_rate: Decimal | None,
    ) -> Optional[Product]:
        if not supplier_id or not name:
            return None

        target_unit = (unit or "ks").strip().lower()
        stmt = select(Product).where(Product.supplier_id == supplier_id)
        stmt = stmt.where(func.lower(Product.name) == name.strip().lower())
        stmt = stmt.where(func.lower(Product.unit) == target_unit)
        stmt = stmt.where(Product.unit_price == Decimal(str(unit_price)))
        if vat_rate is not None:
            stmt = stmt.where(Product.vat_rate == Decimal(str(vat_rate)))
        return (await self.db.execute(stmt)).scalars().first()

    @staticmethod
    def to_schema(row: Product) -> ProductSchema:
        return ProductSchema.model_validate(row, from_attributes=True)


__all__ = ["ProductRepository", "ProductCategoryRepository"]
