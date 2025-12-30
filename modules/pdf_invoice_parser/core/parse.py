from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any, Dict, List, Tuple

from pypdf import PdfReader

SKU_PATTERN = re.compile(r"(?P<sku>(RID\d{6,}|103\d{6,}))\b")
PRICE_PATTERN = re.compile(
    r"(?P<unit>[0-9\s]+\d,[0-9]{2})\s+"
    r"(?P<qty>\d+(?:,\d{1,3})?)\s+"
    r"(?P<total>[0-9\s]+\d,[0-9]{2})\s+"
    r"(?P<vat>\d{1,2})\s?%$"
)


def _clean_line(raw: str) -> str:
    text = raw.replace("\xa0", " ")
    text = re.sub(r"Strana:\s*\d+\s*/\s*\d+", "", text, flags=re.IGNORECASE)
    text = text.strip()
    return re.sub(r"\s+", " ", text)


def _parse_decimal(value: str, places: int = 2) -> str:
    normalized = value.replace(" ", "").replace(",", ".")
    try:
        num = Decimal(normalized)
    except InvalidOperation:
        return "0.00"
    quant = Decimal("1." + "0" * places)
    return f"{num.quantize(quant)}"


def _parse_qty(value: str) -> str:
    normalized = value.replace(" ", "").replace(",", ".")
    try:
        num = Decimal(normalized)
    except InvalidOperation:
        return "0"
    if num == num.to_integral():
        return str(int(num))
    return str(num.normalize())


def _extract_invoice_number(text: str) -> str | None:
    patterns = [
        r"\binvoice\s*(?:no\.?|#)?\s*([A-Za-z0-9-]+)",
        r"\bfaktura\s*(?:cislo|c\.|#)?\s*([A-Za-z0-9-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _extract_items(lines: List[str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    i = 0

    def _consume_segment(text: str, acc: List[str]):
        if not text:
            return None
        price_match = PRICE_PATTERN.search(text)
        if price_match:
            before = text[: price_match.start()].strip()
            if before:
                acc.append(before)
            return price_match.groupdict()
        acc.append(text.strip())
        return None

    while i < len(lines):
        line = lines[i]
        match = SKU_PATTERN.search(line)
        if not match:
            i += 1
            continue

        sku = match.group("sku")
        first_line = line[:match.start()].strip()
        remainder = line[match.end() :].strip()
        description_parts: List[str] = []
        if first_line:
            description_parts.append(first_line)
        price_data = _consume_segment(remainder, description_parts)
        i += 1

        while price_data is None and i < len(lines):
            price_data = _consume_segment(lines[i], description_parts)
            i += 1

        if not price_data:
            break

        items.append(
            {
                "sku": sku,
                "name": " ".join(description_parts).strip(),
                "unit_price": _parse_decimal(price_data["unit"]),
                "qty": _parse_qty(price_data["qty"]),
                "vat_rate": price_data["vat"].strip(),
                "line_total": _parse_decimal(price_data["total"]),
            }
        )

    return items


def parse_invoice_pdf_bytes(content: bytes) -> Tuple[Dict[str, Any] | None, str | None]:
    if not content:
        return None, "Upload a PDF file."

    reader = PdfReader(BytesIO(content))
    full_text = "\n".join(filter(None, (page.extract_text() or "" for page in reader.pages)))
    if not full_text.strip():
        return None, "No text detected in the PDF."

    lines = [_clean_line(line) for line in full_text.splitlines()]
    lines = [line for line in lines if line]

    invoice_number = _extract_invoice_number(full_text) or "UNKNOWN"
    items = _extract_items(lines)
    warnings: List[str] = []
    if invoice_number == "UNKNOWN":
        warnings.append("Invoice number not detected.")
    if not items:
        warnings.append("No line items detected for the current parser.")

    return {
        "invoice_number": invoice_number,
        "item_count": len(items),
        "line_count": len(lines),
        "items": items,
        "text_sample": full_text[:800],
        "warnings": warnings,
    }, None
