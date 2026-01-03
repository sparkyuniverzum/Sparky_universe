from __future__ import annotations

from typing import Dict, List


_SATELLITES: List[Dict[str, str]] = [
    {
        "id": "sparky-finance-orbit-cz",
        "slug": "finance-orbit",
        "title": "Sparky Finance Orbit · CZ Core",
        "description": "Daily exchange rates and the CNB repo rate in a clean JSON snapshot.",
        "mount": "/satellites/finance-orbit",
        "api": "/satellites/finance-orbit/latest",
        "status": "live",
    }
]


def list_satellites() -> List[Dict[str, str]]:
    return list(_SATELLITES)
