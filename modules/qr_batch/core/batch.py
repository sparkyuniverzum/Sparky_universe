from __future__ import annotations

import csv
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

from modules.qrforge.core.ids import generate_public_id
from modules.qrforge.core.payload import build_identity_payload
from modules.qrforge.core.render import render_qr
from modules.qrforge.core.sign import sign_payload


def _parse_limit(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


MAX_ROWS = _parse_limit("SPARKY_QR_BATCH_MAX_ROWS", 500)
MAX_INPUT_CHARS = _parse_limit("SPARKY_QR_BATCH_MAX_CHARS", 200000)


def _normalize_row(row: List[str]) -> Dict[str, str | None] | None:
    parts = [item.strip() for item in row]
    if not any(parts):
        return None

    name = parts[0] if parts else None
    if not name:
        return None

    supplier = parts[1] if len(parts) > 1 and parts[1] else None
    supplier_sku = parts[2] if len(parts) > 2 and parts[2] else None

    return {
        "name": name,
        "supplier": supplier,
        "supplier_sku": supplier_sku,
    }


def parse_rows(raw_text: str) -> Tuple[List[Dict[str, str | None]], str | None]:
    if len(raw_text) > MAX_INPUT_CHARS:
        return [], f"Input is too large (max {MAX_INPUT_CHARS} characters)."

    rows: List[Dict[str, str | None]] = []
    reader = csv.reader(io.StringIO(raw_text))

    for index, row in enumerate(reader):
        if not row:
            continue

        normalized = _normalize_row(row)
        if not normalized:
            continue

        if index == 0:
            header = [item.lower() for item in row]
            if header and header[0] == "name":
                continue

        rows.append(normalized)
        if len(rows) >= MAX_ROWS:
            return [], f"Too many rows (max {MAX_ROWS})."

    return rows, None


def build_batch_zip(raw_text: str, secret: str) -> Tuple[bytes, int, str | None]:
    rows, error = parse_rows(raw_text)
    if error:
        return b"", 0, error
    if not rows:
        return b"", 0, None

    manifest: List[Dict[str, object]] = []
    files: List[Tuple[str, Path]] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        for index, row in enumerate(rows, start=1):
            public_id = generate_public_id()
            payload = build_identity_payload(
                public_id=public_id,
                name=row.get("name"),
                supplier=row.get("supplier"),
                supplier_sku=row.get("supplier_sku"),
            )
            signature = sign_payload(payload, secret)
            filename = f"{index:03d}_{public_id}.png"
            output_path = base_dir / filename

            render_qr(payload, signature, str(output_path))
            files.append((filename, output_path))
            manifest.append(
                {
                    "filename": filename,
                    "payload": payload,
                    "signature": signature,
                }
            )

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zip_file:
            for filename, path in files:
                zip_file.write(path, arcname=filename)
            zip_file.writestr("manifest.json", json.dumps(manifest, indent=2))

    return zip_buffer.getvalue(), len(manifest), None
