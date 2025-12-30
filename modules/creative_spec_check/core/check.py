from __future__ import annotations

from typing import Any, Dict, List, Tuple

PLATFORM_SPECS = {
    "meta": [
        {"name": "Square feed", "width": 1080, "height": 1080},
        {"name": "Portrait feed", "width": 1080, "height": 1350},
        {"name": "Landscape", "width": 1200, "height": 628},
        {"name": "Stories", "width": 1080, "height": 1920},
    ],
    "google": [
        {"name": "Display medium rectangle", "width": 300, "height": 250},
        {"name": "Display large rectangle", "width": 336, "height": 280},
        {"name": "Leaderboard", "width": 728, "height": 90},
        {"name": "Wide skyscraper", "width": 160, "height": 600},
        {"name": "Half page", "width": 300, "height": 600},
        {"name": "Landscape", "width": 1200, "height": 628},
    ],
    "tiktok": [
        {"name": "Vertical video", "width": 1080, "height": 1920},
    ],
    "linkedin": [
        {"name": "Landscape", "width": 1200, "height": 627},
        {"name": "Square", "width": 1080, "height": 1080},
    ],
    "x": [
        {"name": "Summary large image", "width": 1200, "height": 628},
        {"name": "In-stream", "width": 1600, "height": 900},
    ],
}


def _ratio(width: int, height: int) -> float:
    return round(width / height, 2)


def _match_specs(width: int, height: int, platform: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    specs = PLATFORM_SPECS.get(platform, [])
    matches = []
    near = []
    target_ratio = _ratio(width, height)

    for spec in specs:
        if spec["width"] == width and spec["height"] == height:
            matches.append(spec)
        else:
            spec_ratio = _ratio(spec["width"], spec["height"])
            if abs(spec_ratio - target_ratio) <= 0.05:
                near.append({**spec, "ratio": spec_ratio})

    return matches, near


def check_specs(
    *,
    width: int | None,
    height: int | None,
    platform: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    if not width or not height:
        return None, "Provide width and height."
    if width <= 0 or height <= 0:
        return None, "Width and height must be greater than zero."

    platform = (platform or "meta").strip().lower()
    if platform not in PLATFORM_SPECS:
        platform = "meta"

    ratio = _ratio(width, height)
    orientation = "landscape"
    if ratio == 1:
        orientation = "square"
    elif ratio < 1:
        orientation = "portrait"

    matches, near = _match_specs(width, height, platform)

    warnings: List[str] = []
    if width < 600 or height < 315:
        warnings.append("Creative is below 600x315; may render poorly.")

    return {
        "width": width,
        "height": height,
        "ratio": ratio,
        "orientation": orientation,
        "platform": platform,
        "matches": matches,
        "near_matches": near,
        "warnings": warnings,
    }, None
