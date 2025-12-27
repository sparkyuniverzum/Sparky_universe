# backend/app/core/mappings/suppliers.py
from __future__ import annotations

from typing import Any, Dict

from app.core.mapping import mapper  # proč: společná vrstva
from app.domains.suppliers.model import Supplier as SupplierORM
from app.domains.suppliers.schema import SupplierOut, SupplierCreate, SupplierUpdate


@mapper.register(SupplierORM, SupplierOut)
def supplier_to_out(m: SupplierORM, dst, ctx: Dict[str, Any]) -> SupplierOut:
    return SupplierOut.model_validate(m, from_attributes=True)


@mapper.register(SupplierCreate, SupplierORM)
def supplier_create(dto: SupplierCreate, dst, ctx: Dict[str, Any]) -> SupplierORM:
    data = dto.model_dump(exclude_none=True)
    return SupplierORM(**data)


@mapper.register(SupplierUpdate, SupplierORM)
def supplier_update(dto: SupplierUpdate, dst, ctx: Dict[str, Any]) -> SupplierORM:
    patch = SupplierORM()
    for field, value in dto.model_dump(exclude_none=True).items():
        setattr(patch, field, value)
    return patch
