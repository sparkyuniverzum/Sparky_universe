from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, Tuple, Mapping, Any

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.core.settings import settings
from app.domains.catalog import services as catalog_service
from app.domains.catalog.repositories.product_repository import ProductRepository
from app.domains.catalog.schemas.product import ProductCreate, ProductUpdate
from app.domains.catalog.services.catalog_service import classify_product_category
from app.domains.catalog.utils.catalog_utils import SEED_CATEGORIES
from app.domains.inventory.models.receipt import Receipt as ReceiptORM
from app.domains.inventory.repositories.receipt_repo import ReceiptCRUD
from app.domains.inventory.schemas.receipt import Receipt as ReceiptOut, ReceiptCreate, ReceiptItemCreate
from app.domains.suppliers import service as suppliers_service
from app.domains.suppliers.model import Supplier as SupplierORM
from app.domains.inventory.models.stock_batch import Batch
from app.domains.inventory.models.stock_movement import StockMovement, MovementType
from app.domains.ledger.models.model import StockLedger
from app.domains.ledger.services.service import append_from_movement
from app.domains.accounting.service import post_receipt, reverse_entries, generate_document_number
from app.domains.inventory.status import ReceiptStatus


DEFAULT_CATEGORY_CODE = "doplnky"
if not any(code == DEFAULT_CATEGORY_CODE for code, _ in SEED_CATEGORIES):
    DEFAULT_CATEGORY_CODE = SEED_CATEGORIES[0][0]


async def _create_batch_and_in_movement(
    db: AsyncSession,
    *,
    product_id: str,
    qty: Decimal,
    receipt_id: str,
    label: str | None = None,
    note: str | None = None,
    unit_cost: Decimal | None = None,
) -> None:
    batch = Batch(
        label=label,
        product_id=product_id,
        qty_in=qty,
        qty_sold=Decimal("0"),
        receipt_id=receipt_id,
        unit_cost=unit_cost or Decimal("0"),
    )
    db.add(batch)
    await db.flush()

    movement = StockMovement(
        product_id=product_id,
        batch_id=batch.id,
        qty=qty,
        type=MovementType.IN,
        note=note or "receipt",
        reason="receipt",
    )
    db.add(movement)
    await db.flush()
    await append_from_movement(db, movement=movement, reason="receipt")
    db.add(
        StockLedger(
            product_id=product_id,
            batch_id=batch.id,
            receipt_id=receipt_id,
            sale_id=None,
            movement_id=movement.id,
            direction="IN",
            qty=qty,
            note=note or "receipt",
        )
    )


async def _ensure_product_for_item(
    db: AsyncSession,
    *,
    receipt_supplier_id: str | None,
    item: ReceiptItemCreate,
    repo: ProductRepository,
) -> str | None:
    if item.product_id:
        return item.product_id

    matching = await repo.find_matching_by_attributes(
        supplier_id=receipt_supplier_id,
        name=item.product_name,
        unit=item.unit,
        unit_price=item.unit_price,
        vat_rate=item.vat_rate,
    )
    if matching:
        if not item.product_name:
            item.product_name = matching.name
        return str(matching.id)

    if not item.product_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="product_name is required when product_id is missing",
        )

    product_payload_data = {
        "name": item.product_name,
        "unit": item.unit or "ks",
        "unit_price": item.unit_price,
        "supplier_id": receipt_supplier_id,
        "supplier_sku": item.supplier_sku,
        "is_active": True,
    }
    if item.vat_rate is not None:
        product_payload_data["vat_rate"] = item.vat_rate
    if item.barcode:
        product_payload_data["barcode"] = item.barcode
    if item.category_id:
        product_payload_data["category_id"] = item.category_id
    elif item.category:
        product_payload_data["category"] = item.category
    else:
        inferred = classify_product_category(
            name=item.product_name,
            supplier_sku=item.supplier_sku,
            supplier_id=receipt_supplier_id,
        )
        product_payload_data["category"] = inferred or DEFAULT_CATEGORY_CODE

    product_payload = ProductCreate(**product_payload_data)
    created = await catalog_service.create_product(
        db,
        product_payload,
    )
    return str(created.id)


async def create_receipt(
    db: AsyncSession,
    payload: ReceiptCreate,
    *,
    batch_label: str | None = None,
) -> ReceiptOut:
    crud = ReceiptCRUD(db)
    product_repo = ProductRepository(db)
    net_total = Decimal("0")
    vat_total = Decimal("0")
    for item in payload.items:
        if item.product_id:
            if not item.product_name:
                product = await catalog_service.get_product(db, item.product_id)
                if product:
                    item.product_name = getattr(product, "name", None)
        else:
            product_id = await _ensure_product_for_item(
                db,
                receipt_supplier_id=payload.supplier_id,
                item=item,
                repo=product_repo,
            )
            item.product_id = product_id
            if not item.product_id:
                raise DomainError(
                    "Product could not be resolved for receipt item",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    code="product_missing",
                )
        item.qty = Decimal(str(item.qty))
        item.unit_price = Decimal(str(item.unit_price))
        if item.vat_rate is not None:
            item.vat_rate = Decimal(str(item.vat_rate))
        line_net = item.qty * item.unit_price
        net_total += line_net
        if item.vat_rate is not None:
            vat_total += (line_net * Decimal(str(item.vat_rate)) / Decimal("100")).quantize(Decimal("0.01"))

    receipt = await crud.create(payload)
    receipt.status = ReceiptStatus.POSTED
    db.add(receipt)
    if getattr(receipt, "document_number", None) is None:
        receipt.document_number = await generate_document_number(db, code="RECEIPT")
        db.add(receipt)

    for item in payload.items:
        if not item.product_id:
            continue
        await _create_batch_and_in_movement(
            db,
            product_id=item.product_id,
            qty=Decimal(str(item.qty)),
            receipt_id=receipt.id,
            label=batch_label,
            note=item.note,
            unit_cost=Decimal(str(item.unit_price)),
        )

    await db.flush()
    await db.refresh(receipt)

    # Accounting: zaúčtuj příjemku (zásoby / závazky + DPH)
    await post_receipt(db, receipt, amount=net_total, vat_amount=vat_total)

    return ReceiptOut.model_validate(receipt)


async def get_receipt(db: AsyncSession, receipt_id: str) -> ReceiptOut:
    crud = ReceiptCRUD(db)
    obj = await crud.get(receipt_id)
    return ReceiptOut.model_validate(obj)


async def list_receipts(
    db: AsyncSession,
    *,
    limit: int = 100,
    offset: int = 0,
    supplier_id: Optional[str] = None,
    q: Optional[str] = None,
) -> Tuple[List[ReceiptORM], int]:
    crud = ReceiptCRUD(db)
    rows, total = await crud.list(
        limit=limit,
        offset=offset,
        supplier_id=supplier_id,
        q=q,
    )
    return rows, total


async def void_receipt(db: AsyncSession, receipt_id: str) -> ReceiptOut:
    crud = ReceiptCRUD(db)
    receipt = await crud.get(receipt_id)
    if not receipt:
        raise DomainError("Receipt not found", status_code=status.HTTP_404_NOT_FOUND, code="receipt_not_found")
    current_status = getattr(receipt, "status", "")
    if current_status == ReceiptStatus.VOID:
        return ReceiptOut.model_validate(receipt)
    if current_status != ReceiptStatus.POSTED:
        raise DomainError(
            "receipt not posted",
            status_code=status.HTTP_400_BAD_REQUEST,
            code="receipt_not_posted",
        )

    await reverse_entries(db, document_type="receipt", document_id=str(receipt.id), note="receipt void")
    receipt.status = ReceiptStatus.VOID
    db.add(receipt)
    await db.flush()
    await db.refresh(receipt)
    return ReceiptOut.model_validate(receipt)


async def _resolve_supplier_id(db: AsyncSession, supplier_name: str) -> str:
    exact = await db.execute(
        select(SupplierORM)
        .where(func.lower(SupplierORM.name) == supplier_name.lower())
        .limit(1)
    )
    exact_row = exact.scalars().first()
    if exact_row:
        return exact_row.id  # type: ignore[attr-defined]

    found = await suppliers_service.find_supplier_by_name(db, supplier_name)
    if found:
        return found.id

    if settings.pdf_import_supplier_id:
        return settings.pdf_import_supplier_id

    fallback = await suppliers_service.list_suppliers(
        db,
        q=None,
        limit=1,
        offset=0,
    )
    if not fallback.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier for PDF import not found. Configure PDF_IMPORT_SUPPLIER_ID or create supplier.",
        )
    return fallback.items[0].id


def _as_number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


async def import_receipt_from_parsed_pdf(
    db: AsyncSession,
    parsed: Mapping[str, Any],
) -> ReceiptOut:
    items = parsed.get("items") or []
    if not items:
        raise DomainError(
            "Parsed PDF does not contain any items",
            status_code=status.HTTP_400_BAD_REQUEST,
            code="empty_pdf_items",
        )

    supplier_name = parsed.get("supplier", {}).get("name") or "OdKarla.cz"
    supplier_id = await _resolve_supplier_id(db, supplier_name)

    receipt_items: list[ReceiptItemCreate] = []
    for item in items:
        qty = _as_number(item.get("qty"), 1.0)
        unit_price = _as_number(item.get("unit_price"), 0.0)
        vat_rate = _as_number(item.get("vat_rate"), 0.0)
        supplier_sku = item.get("supplier_sku")
        product_name = item.get("product_name") or "Neznámý produkt"

        inferred_category = classify_product_category(
            name=product_name,
            supplier_sku=supplier_sku,
            supplier_id=supplier_id,
        )
        target_category = inferred_category or DEFAULT_CATEGORY_CODE

        existing_product_id: str | None = None
        item_category_id: str | None = None
        if supplier_sku:
            existing = await catalog_service.get_product_by_supplier_sku(
                db, None, supplier_sku
            )
            if existing:
                existing_product_id = str(existing.id)
                if not getattr(existing, "category", None):
                    updated = await catalog_service.update_product(
                        db,
                        str(existing.id),
                        ProductUpdate(category=target_category),
                    )
                    item_category_id = updated.category_id
                else:
                    item_category_id = existing.category_id
        else:
            item_category_id = None

        if existing_product_id:
            product_id = existing_product_id
        else:
            product_payload = ProductCreate(
                name=product_name,
                unit="ks",
                unit_price=str(unit_price),
                vat_rate=str(vat_rate),
                supplier_id=supplier_id,
                supplier_sku=supplier_sku,
                is_active=True,
                category=target_category,
            )
            try:
                created_product = await catalog_service.create_product(
                    db, product_payload, actor_id=settings.dev_default_actor
                )
            except DomainError as exc:
                if supplier_sku:
                    existing = await catalog_service.get_product_by_supplier_sku(
                        db, None, supplier_sku
                    )
                    if existing:
                        product_id = str(existing.id)
                        receipt_items.append(
                            ReceiptItemCreate(
                                product_id=product_id,
                                product_name=product_name,
                                supplier_sku=supplier_sku,
                                qty=qty,
                                unit_price=unit_price,
                                vat_rate=vat_rate,
                                note="import",
                                category=target_category,
                                category_id=item_category_id,
                            )
                        )
                        continue
                raise exc
            item_category_id = created_product.category_id
            product_id = str(created_product.id)

        receipt_items.append(
            ReceiptItemCreate(
                product_id=product_id,
                product_name=product_name,
                supplier_sku=supplier_sku,
                qty=qty,
                unit_price=unit_price,
                vat_rate=vat_rate,
                note="import",
                category=target_category,
                category_id=item_category_id,
            )
        )

    receipt_payload = ReceiptCreate(
        supplier_id=supplier_id,
        note="PDF import",
        items=receipt_items,
    )

    return await create_receipt(db, receipt_payload)


__all__ = [
    "create_receipt",
    "get_receipt",
    "list_receipts",
    "import_receipt_from_parsed_pdf",
]
