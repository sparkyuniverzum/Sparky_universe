# backend/app/core/mappings/products.py
from __future__ import annotations

from app.core.mapping import mapper
from app.domains.catalog.models.product import Product as ProductORM
from app.domains.catalog.schemas.product import Product as ProductOut, ProductCreate, ProductUpdate


@mapper.register(ProductORM, ProductOut)
def product_to_out(m: ProductORM, dst, ctx):
    return ProductOut.model_validate(m, from_attributes=True)


@mapper.register(ProductCreate, ProductORM)
def product_create(dto: ProductCreate, dst, ctx):
    data = dto.model_dump(exclude_none=True)
    return ProductORM(**data)


@mapper.register(ProductUpdate, ProductORM)
def product_update(dto: ProductUpdate, dst, ctx):
    patch = ProductORM()
    for field, value in dto.model_dump(exclude_none=True).items():
        setattr(patch, field, value)
    return patch
