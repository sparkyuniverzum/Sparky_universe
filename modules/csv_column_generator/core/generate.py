from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple


def _split_choices(value: str | None) -> List[str]:
    if not value:
        return []
    items: List[str] = []
    cleaned = value.replace("\r", "").replace(",", "\n")
    for line in cleaned.split("\n"):
        item = line.strip()
        if item:
            items.append(item)
    return items


def generate_column(
    *,
    mode: str,
    count: int,
    start: int,
    step: int,
    width: int,
    min_value: int,
    max_value: int,
    choices: str | None,
    unique: bool,
    prefix: str | None,
    suffix: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if count <= 0 or count > 5000:
        return None, "Count must be between 1 and 5000."
    if width < 0 or width > 12:
        return None, "Width must be between 0 and 12."

    prefix_text = (prefix or "").strip()
    suffix_text = (suffix or "").strip()
    values: List[str] = []

    if mode == "sequence":
        if step == 0:
            return None, "Step cannot be zero."
        for idx in range(count):
            value = start + step * idx
            text = str(value)
            if width > 0:
                text = text.zfill(width)
            values.append(f"{prefix_text}{text}{suffix_text}")
    elif mode == "random_int":
        if min_value > max_value:
            return None, "Min must be smaller than max."
        if unique and (max_value - min_value + 1) < count:
            return None, "Range is too small for unique values."
        picks: List[int]
        if unique:
            picks = random.sample(range(min_value, max_value + 1), count)
        else:
            picks = [random.randint(min_value, max_value) for _ in range(count)]
        for pick in picks:
            values.append(f"{prefix_text}{pick}{suffix_text}")
    elif mode == "choice":
        options = _split_choices(choices)
        if not options:
            return None, "Add at least one choice."
        if unique and count > len(options):
            return None, "Not enough choices for unique values."
        picks = random.sample(options, count) if unique else [random.choice(options) for _ in range(count)]
        for pick in picks:
            values.append(f"{prefix_text}{pick}{suffix_text}")
    else:
        return None, "Unsupported mode."

    return {
        "count": len(values),
        "mode": mode,
        "values": values,
        "csv": "\n".join(values),
    }, None
