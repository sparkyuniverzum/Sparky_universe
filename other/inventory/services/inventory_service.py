"""Aggregator for inventory-related services (stock, receipts, movements)."""
from app.domains.inventory.services.stock_service import get_stock
from app.domains.inventory.services.receipt_service import (
    create_receipt,
    get_receipt,
    list_receipts,
    import_receipt_from_parsed_pdf,
)
from app.domains.inventory.services.stock_movement_service import (
    create_movement,
    list_movements,
    MovementType,
)
from app.domains.inventory.services.allocation import (
    plan_allocation_fifo,
    apply_allocation_movements,
    allocate_sale_item,
    InsufficientStock,
)

__all__ = [
    "get_stock",
    "create_receipt",
    "get_receipt",
    "list_receipts",
    "import_receipt_from_parsed_pdf",
    "create_movement",
    "list_movements",
    "MovementType",
    "plan_allocation_fifo",
    "apply_allocation_movements",
    "allocate_sale_item",
    "InsufficientStock",
]
