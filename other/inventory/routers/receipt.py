from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.common import ListResponse, DetailResponse
from app.core.audit import AuditRoute
from app.core.dependencies import get_session
from app.domains.inventory.schemas.receipt import Receipt, ReceiptCreate
from app.core.dependencies.permissions import require_warehouse
from app.domains.inventory import services as receipts_service
from app.integrations.pdf import parse_invoice_pdf_bytes
from app.api.responses import get_response_factory, ResponseFactory

router = APIRouter(
    prefix="/receipts",
    tags=["receipts"],
    route_class=AuditRoute,
    dependencies=[Depends(require_warehouse)],
)

MAX_PDF_SIZE = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"application/pdf"}


@router.get("", response_model=ListResponse[Receipt])
async def list_receipts(
    limit: int = 100,
    offset: int = 0,
    supplier_id: Optional[str] = None,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
) -> dict:
    rows, total = await receipts_service.list_receipts(
        db=db,
        limit=limit,
        offset=offset,
        supplier_id=supplier_id,
        q=q,
    )

    payload = {
        "data": [Receipt.model_validate(r).model_dump(mode="json") for r in rows],
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }
    return responses.list(payload)


@router.get("/{receipt_id}", response_model=DetailResponse[Receipt])
async def get_receipt(
    receipt_id: str,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
) -> dict:
    obj = await receipts_service.get_receipt(db, receipt_id)
    return responses.detail({"data": Receipt.model_validate(obj).model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@router.post(
    "",
    response_model=DetailResponse[Receipt],
    status_code=status.HTTP_201_CREATED,
)
async def create_receipt(
    request: Request,
    payload: ReceiptCreate,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
) -> dict:
    obj = await receipts_service.create_receipt(db, payload)
    await db.commit()
    return responses.detail({"data": Receipt.model_validate(obj).model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@router.post(
    "/import-pdf",
    response_model=DetailResponse[Receipt],
    status_code=status.HTTP_201_CREATED,
)
async def import_pdf(
    file: UploadFile,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
) -> dict:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")

    content = await file.read(MAX_PDF_SIZE + 1)
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF is too large (max 5 MB)")

    try:
        parsed = parse_invoice_pdf_bytes(content)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to parse PDF: {exc}") from exc

    created = await receipts_service.import_receipt_from_parsed_pdf(db, parsed)
    await db.commit()
    return responses.detail({"data": Receipt.model_validate(created).model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@router.post("/{receipt_id}/void", response_model=DetailResponse[Receipt])
async def void_receipt(
    receipt_id: str,
    db: AsyncSession = Depends(get_session),
    responses: ResponseFactory = Depends(get_response_factory),
) -> dict:
    obj = await receipts_service.void_receipt(db, receipt_id)
    await db.commit()
    return responses.detail({"data": Receipt.model_validate(obj).model_dump(mode="json")}, status_code=status.HTTP_200_OK)


__all__ = ["router"]
