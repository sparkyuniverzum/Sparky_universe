from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import os
import hmac
import hashlib
from decimal import Decimal
from typing import Iterable

import segno
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.domains.catalog.repositories.product_repository import ProductRepository
from app.core.errors import DomainError
from app.core.settings import get_settings
from app.domains.inventory.models.stock_movement import StockMovement, MovementType
from app.domains.inventory.services.stock_service import _resolve_col

QR_DIR = Path(os.getenv("QR_DIR", "data/qr"))
_settings = get_settings()


def _build_payload(product) -> dict:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "v": 1,  # payload schema version
        "ts": now,
        "data": {
            "pid": getattr(product, "public_id", None) or str(product.id),
            "sku": getattr(product, "supplier_sku", None),
            "rid": getattr(product, "supplier_id", None),
            "name": getattr(product, "name", None),
            "unit": getattr(product, "unit", None),
            "price": str(getattr(product, "unit_price", "")),
            "vat_rate": str(getattr(product, "vat_rate", "")),
        },
    }


def _sign_payload(payload: dict) -> tuple[str, str]:
    """Return (payload_json, signature) using HMAC over canonical JSON."""
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    secret = (_settings.JWT_SECRET_KEY or "dev").encode("utf-8")
    sig = hmac.new(secret, payload_json.encode("utf-8"), hashlib.sha256).hexdigest()
    return payload_json, sig


def _unlink_safe(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


async def generate_product_qr(
    db: AsyncSession,
    product_id: str,
    *,
    force: bool = False,
) -> dict:
    repo = ProductRepository(db)
    product = await repo.get_by_id_or_public(product_id)
    if not product:
        raise DomainError("Product not found", status_code=404, code="product_not_found")

    payload_dict = _build_payload(product)
    payload_json, signature = _sign_payload(payload_dict)

    # reuse existing only if not forced and payload matches
    if getattr(product, "qr_payload", None) and not force:
        try:
            if json.loads(product.qr_payload) == payload_dict:  # type: ignore[attr-defined]
                payload_json = product.qr_payload  # type: ignore[attr-defined]
        except Exception:
            pass

    QR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{product.id}_{signature[:10]}.png"
    filepath = QR_DIR / filename

    # remove old file if path changed
    old_url = getattr(product, "qr_image_url", None)
    if old_url:
        old_name = old_url.split("/qr/")[-1]
        _unlink_safe(QR_DIR / old_name)

    qr = segno.make(payload_json)
    qr.save(filepath, scale=4)

    product.qr_payload = payload_json  # type: ignore[attr-defined]
    product.qr_image_url = f"/qr/{filename}"  # type: ignore[attr-defined]
    db.add(product)
    await db.flush()
    await db.refresh(product)

    return {
        "payload": payload_json,
        "image_url": product.qr_image_url,
        "signature": signature,
    }


async def cleanup_qr_if_no_stock(db: AsyncSession, product_ids: Iterable[str]) -> list[str]:
    """Remove QR for products whose on-hand qty <= 0 after stock movements."""
    cleaned: list[str] = []
    ids = [pid for pid in set(product_ids) if pid]
    if not ids:
        return cleaned

    col_pid = _resolve_col(StockMovement, ["product_id"])
    col_qty = _resolve_col(StockMovement, ["qty"])
    signed_qty = case(
        (StockMovement.type == MovementType.IN, func.abs(col_qty)),
        (StockMovement.type == MovementType.OUT, -func.abs(col_qty)),
        else_=col_qty,
    )

    qty_rows = (
        await db.execute(
            select(col_pid, func.coalesce(func.sum(signed_qty), 0))
            .where(col_pid.in_(ids))
            .group_by(col_pid)
        )
    ).all()
    qty_map = {str(pid): Decimal(q) for pid, q in qty_rows}

    repo = ProductRepository(db)
    for pid in ids:
        remaining = qty_map.get(pid, Decimal("0"))
        if remaining > Decimal("0"):
            continue
        product = await repo.get_by_id_or_public(pid)
        if not product:
            continue
        old_url = getattr(product, "qr_image_url", None)
        if old_url:
            old_name = old_url.split("/qr/")[-1]
            _unlink_safe(QR_DIR / old_name)
        product.qr_payload = None  # type: ignore[attr-defined]
        product.qr_image_url = None  # type: ignore[attr-defined]
        db.add(product)
        cleaned.append(str(product.id))
    return cleaned


__all__ = ["generate_product_qr", "cleanup_qr_if_no_stock"]
