# backend/app/core/mappings/receipts.py
from __future__ import annotations

from app.core.mapping import mapper
from app.domains.inventory.models.receipt import Receipt as ReceiptORM, ReceiptItem as ReceiptItemORM
from app.domains.inventory.schemas.receipt import Receipt as ReceiptSchema, ReceiptItem as ReceiptItemSchema


@mapper.register(ReceiptItemORM, ReceiptItemSchema)
def receipt_item_to_schema(src: ReceiptItemORM, dst, ctx) -> ReceiptItemSchema:
    return ReceiptItemSchema.model_validate(src, from_attributes=True)


@mapper.register(ReceiptORM, ReceiptSchema)
def receipt_to_schema(src: ReceiptORM, dst, ctx) -> ReceiptSchema:
    # model_validate(..., from_attributes=True) je nastavené ve schema
    return ReceiptSchema.model_validate(src, from_attributes=True)
