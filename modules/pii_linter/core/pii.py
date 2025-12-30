from __future__ import annotations

import csv
import io
import re
from typing import Dict, List, Tuple


MAX_ROWS = 5000
MAX_COLS = 200
MAX_SAMPLES = 3
MAX_MATCHES_PER_CELL = 5
NULL_TOKENS = {"", "null", "none", "na", "n/a", "nan"}

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
CARD_RE = re.compile(r"(?:\d[ -]?){13,19}")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


class _DefaultDialect(csv.Dialect):
    delimiter = ","
    quotechar = '"'
    escapechar = None
    doublequote = True
    skipinitialspace = False
    lineterminator = "\n"
    quoting = csv.QUOTE_MINIMAL


def _sniff_dialect(raw_text: str) -> csv.Dialect:
    sample = raw_text[:2048]
    try:
        return csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
    except csv.Error:
        return _DefaultDialect()


def _is_null(value: str) -> bool:
    return value.strip().lower() in NULL_TOKENS


def _mask_generic(value: str) -> str:
    value = value.strip()
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


def _mask_email(value: str) -> str:
    local, _, domain = value.partition("@")
    if not domain:
        return _mask_generic(value)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + ("*" * (len(local) - 2)) + local[-1]
    return f"{masked_local}@{domain}"


def _mask_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) <= 2:
        return "*" * len(digits)
    return "*" * (len(digits) - 2) + digits[-2:]


def _mask_card(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) <= 4:
        return "*" * len(digits)
    return "*" * (len(digits) - 4) + digits[-4:]


def _mask_iban(value: str) -> str:
    cleaned = re.sub(r"\s+", "", value).upper()
    if len(cleaned) <= 8:
        return "*" * len(cleaned)
    return cleaned[:4] + ("*" * (len(cleaned) - 8)) + cleaned[-4:]


def _mask_ip(value: str) -> str:
    parts = value.strip().split(".")
    if len(parts) != 4:
        return _mask_generic(value)
    return ".".join(parts[:3] + ["***"])


def _luhn_check(value: str) -> bool:
    digits = [int(ch) for ch in value if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    reverse = list(reversed(digits))
    for idx, digit in enumerate(reverse):
        if idx % 2 == 1:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return total % 10 == 0


def _iban_check(value: str) -> bool:
    cleaned = re.sub(r"\s+", "", value).upper()
    if not IBAN_RE.fullmatch(cleaned):
        return False
    rearranged = cleaned[4:] + cleaned[:4]
    digits = ""
    for ch in rearranged:
        if ch.isdigit():
            digits += ch
        elif "A" <= ch <= "Z":
            digits += str(ord(ch) - 55)
        else:
            return False
    remainder = 0
    for ch in digits:
        remainder = (remainder * 10 + int(ch)) % 97
    return remainder == 1


def _valid_ip(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def _read_csv(
    raw_text: str, *, has_header: bool
) -> Tuple[List[str] | None, List[List[str]] | None, bool, str | None]:
    if not raw_text.strip():
        return None, None, False, "CSV is empty."

    dialect = _sniff_dialect(raw_text)
    reader = csv.reader(io.StringIO(raw_text), dialect=dialect)
    rows: List[List[str]] = []
    header: List[str] | None = None
    truncated = False

    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue
        if header is None and has_header:
            header = [cell.strip() or f"column_{idx + 1}" for idx, cell in enumerate(row)]
            continue
        rows.append(row)
        if len(rows) >= MAX_ROWS:
            truncated = True
            break

    if header is None:
        max_cols = max((len(row) for row in rows), default=0)
        header = [f"column_{idx + 1}" for idx in range(max_cols)]
    else:
        max_cols = max((len(row) for row in rows), default=len(header))
        if max_cols > len(header):
            header.extend(
                f"column_{idx + 1}" for idx in range(len(header), max_cols)
            )

    if len(header) > MAX_COLS:
        return None, None, False, f"Too many columns (limit {MAX_COLS})."

    return header, rows, truncated, None


def scan_pii(
    raw_text: str,
    *,
    has_header: bool = True,
) -> Tuple[Dict[str, object] | None, str | None]:
    header, rows, truncated, error = _read_csv(raw_text, has_header=has_header)
    if error or header is None or rows is None:
        return None, error

    col_count = len(header)
    results: List[Dict[str, object]] = []
    totals = {"email": 0, "phone": 0, "iban": 0, "card": 0, "ip": 0}

    for idx in range(col_count):
        results.append(
            {
                "index": idx + 1,
                "name": header[idx],
                "counts": {"email": 0, "phone": 0, "iban": 0, "card": 0, "ip": 0},
                "samples": {"email": [], "phone": [], "iban": [], "card": [], "ip": []},
            }
        )

    for row in rows:
        for idx in range(col_count):
            cell = row[idx] if idx < len(row) else ""
            if _is_null(cell):
                continue
            value = cell.strip()
            if not value:
                continue

            matches = 0
            for match in EMAIL_RE.findall(value):
                if matches >= MAX_MATCHES_PER_CELL:
                    break
                masked = _mask_email(match)
                column = results[idx]
                column["counts"]["email"] += 1
                totals["email"] += 1
                if len(column["samples"]["email"]) < MAX_SAMPLES:
                    column["samples"]["email"].append(masked)
                matches += 1

            for match in PHONE_RE.findall(value):
                if matches >= MAX_MATCHES_PER_CELL:
                    break
                digits = re.sub(r"\D", "", match)
                if not (7 <= len(digits) <= 15):
                    continue
                masked = _mask_phone(match)
                column = results[idx]
                column["counts"]["phone"] += 1
                totals["phone"] += 1
                if len(column["samples"]["phone"]) < MAX_SAMPLES:
                    column["samples"]["phone"].append(masked)
                matches += 1

            for match in IBAN_RE.findall(value.upper()):
                if matches >= MAX_MATCHES_PER_CELL:
                    break
                if not _iban_check(match):
                    continue
                masked = _mask_iban(match)
                column = results[idx]
                column["counts"]["iban"] += 1
                totals["iban"] += 1
                if len(column["samples"]["iban"]) < MAX_SAMPLES:
                    column["samples"]["iban"].append(masked)
                matches += 1

            for match in CARD_RE.findall(value):
                if matches >= MAX_MATCHES_PER_CELL:
                    break
                digits = re.sub(r"\D", "", match)
                if not _luhn_check(digits):
                    continue
                masked = _mask_card(match)
                column = results[idx]
                column["counts"]["card"] += 1
                totals["card"] += 1
                if len(column["samples"]["card"]) < MAX_SAMPLES:
                    column["samples"]["card"].append(masked)
                matches += 1

            for match in IP_RE.findall(value):
                if matches >= MAX_MATCHES_PER_CELL:
                    break
                if not _valid_ip(match):
                    continue
                masked = _mask_ip(match)
                column = results[idx]
                column["counts"]["ip"] += 1
                totals["ip"] += 1
                if len(column["samples"]["ip"]) < MAX_SAMPLES:
                    column["samples"]["ip"].append(masked)
                matches += 1

    return {
        "rows": len(rows),
        "columns": col_count,
        "null_tokens": sorted(token for token in NULL_TOKENS if token),
        "truncated": truncated,
        "totals": totals,
        "scan": results,
    }, None
