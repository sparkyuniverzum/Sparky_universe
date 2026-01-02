from __future__ import annotations

import uuid
from typing import Any, Dict, List, Tuple

ALPHABETS = {
    "base36": "0123456789abcdefghijklmnopqrstuvwxyz",
    "base62": "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
}


def _split_list(value: str | None) -> List[str]:
    if not value:
        return []
    items: List[str] = []
    cleaned = value.replace("\r", "").replace(",", "\n")
    for line in cleaned.split("\n"):
        item = line.strip()
        if item:
            items.append(item)
    return items


def _encode(number: int, alphabet: str) -> str:
    if number == 0:
        return alphabet[0]
    base = len(alphabet)
    chars: List[str] = []
    while number:
        number, rem = divmod(number, base)
        chars.append(alphabet[rem])
    return "".join(reversed(chars))


def shorten_uuids(
    *,
    uuid_list: str | None,
    encoding: str,
    count: int,
    pad: int,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if pad < 0 or pad > 32:
        return None, "Pad must be between 0 and 32."
    items = _split_list(uuid_list)
    generated = False
    if not items:
        if count <= 0 or count > 5000:
            return None, "Count must be between 1 and 5000."
        generated = True
        items = [str(uuid.uuid4()) for _ in range(count)]

    alphabet = ALPHABETS.get(encoding, ALPHABETS["base62"])

    results: List[Dict[str, str]] = []
    invalid: List[str] = []
    for raw in items:
        try:
            parsed = uuid.UUID(raw.strip())
        except ValueError:
            invalid.append(raw)
            continue
        short = _encode(parsed.int, alphabet)
        if pad > 0:
            short = short.rjust(pad, alphabet[0])
        results.append({"uuid": str(parsed), "short": short})

    if not results:
        return None, "No valid UUIDs found."

    return {
        "count": len(results),
        "encoding": encoding,
        "pad": pad if pad > 0 else None,
        "generated": generated,
        "results": results,
        "invalid": invalid,
    }, None
