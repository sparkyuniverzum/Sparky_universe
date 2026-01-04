from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


STAR_ORDER = ["governance", "program", "supply", "treasury", "risk"]

STAR_DEFS: Dict[str, Dict[str, Any]] = {
    "governance": {
        "name": "Governance Star",
        "question": "Are the rules shifting?",
        "roles": ["token_holder", "validator", "builder"],
    },
    "program": {
        "name": "Program Star",
        "question": "Is protocol behavior changing?",
        "roles": ["builder", "operator"],
    },
    "supply": {
        "name": "Supply Star",
        "question": "Is supply pressure shifting?",
        "roles": ["token_holder", "market_maker"],
    },
    "treasury": {
        "name": "Treasury Star",
        "question": "Is capital moving?",
        "roles": ["treasury", "operator"],
    },
    "risk": {
        "name": "Risk Star",
        "question": "Is systemic risk rising?",
        "roles": ["observer"],
    },
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def state_for_impact(impact: int) -> str:
    if impact >= 5:
        return "critical"
    if impact >= 3:
        return "pulsing"
    if impact >= 1:
        return "glowing"
    return "quiet"


def adjust_impact(base: int, recent_count: int) -> int:
    impact = max(0, min(5, base))
    if impact <= 0:
        return 0
    if recent_count >= 4:
        impact = min(5, impact + 1)
    if recent_count >= 8:
        impact = min(5, impact + 1)
    return impact


def build_star_snapshot(
    star_id: str,
    history: List[Dict[str, Any]],
    *,
    recent_events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    base = 0
    last_change = None
    if history:
        latest = history[0]
        base = int(latest.get("impact_level", 0) or 0)
        last_change = latest.get("valid_from") or latest.get("created_at")

    impact = adjust_impact(base, len(recent_events))
    state = state_for_impact(impact)
    info = STAR_DEFS.get(star_id, {})
    return {
        "id": star_id,
        "name": info.get("name", star_id.title()),
        "question": info.get("question", ""),
        "impact_level": impact,
        "state": state,
        "last_change_at": last_change,
        "history": history,
    }


def build_risk_snapshot(snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
    now = _utc_now()
    high = [star for star in snapshots if star.get("impact_level", 0) >= 3]
    max_impact = max((star.get("impact_level", 0) for star in snapshots), default=0)
    impact = 0
    if max_impact >= 5:
        impact = 5
    elif len(high) >= 2 and max_impact >= 3:
        impact = 4
    elif max_impact >= 4:
        impact = 3
    elif len(high) == 1:
        impact = 2

    state = state_for_impact(impact)
    info = STAR_DEFS["risk"]
    return {
        "id": "risk",
        "name": info["name"],
        "question": info["question"],
        "impact_level": impact,
        "state": state,
        "last_change_at": now.isoformat(),
        "history": [],
    }


def recent_window(hours: int = 24) -> datetime:
    return _utc_now() - timedelta(hours=hours)
