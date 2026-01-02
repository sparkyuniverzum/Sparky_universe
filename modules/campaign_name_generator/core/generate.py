from __future__ import annotations

import itertools
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _split_list(value: str | None) -> List[str]:
    if not value:
        return []
    items: List[str] = []
    for chunk in value.replace("\n", ",").split(","):
        item = chunk.strip()
        if item:
            items.append(item)
    return items


def _tokenize(value: str | None) -> List[str]:
    return [item.replace(" ", "-") for item in _split_list(value)]


def _date_label(value: str | None) -> str:
    if value and value.strip():
        return value.strip()
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def generate_campaign_names(
    *,
    brand: str | None,
    channels: str | None,
    offers: str | None,
    regions: str | None,
    objective: str | None,
    date: str | None,
    separator: str,
    limit: int,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if limit <= 0 or limit > 5000:
        return None, "Limit must be between 1 and 5000."
    brand_token = (brand or "brand").strip().replace(" ", "-")
    channel_list = _tokenize(channels) or ["channel"]
    offer_list = _tokenize(offers) or ["offer"]
    region_list = _tokenize(regions) or ["region"]
    objective_token = (objective or "objective").strip().replace(" ", "-")
    date_token = _date_label(date)

    combos = itertools.product(channel_list, offer_list, region_list)
    names: List[str] = []
    for channel, offer, region in combos:
        parts = [brand_token, channel, objective_token, offer, region, date_token]
        names.append(separator.join(parts))
        if len(names) >= limit:
            break

    return {
        "count": len(names),
        "brand": brand_token,
        "objective": objective_token,
        "date": date_token,
        "names": names,
    }, None
