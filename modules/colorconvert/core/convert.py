from __future__ import annotations

from typing import Any, Dict, Tuple

COLOR_MAP = {
    "black": "#000000",
    "white": "#ffffff",
    "red": "#ff0000",
    "lime": "#00ff00",
    "blue": "#0000ff",
    "yellow": "#ffff00",
    "cyan": "#00ffff",
    "magenta": "#ff00ff",
    "silver": "#c0c0c0",
    "gray": "#808080",
    "maroon": "#800000",
    "olive": "#808000",
    "green": "#008000",
    "purple": "#800080",
    "teal": "#008080",
    "navy": "#000080",
    "orange": "#ffa500",
    "pink": "#ffc0cb",
    "brown": "#a52a2a",
    "gold": "#ffd700",
    "coral": "#ff7f50",
    "salmon": "#fa8072",
    "indigo": "#4b0082",
    "violet": "#ee82ee",
    "turquoise": "#40e0d0",
    "skyblue": "#87ceeb",
    "steelblue": "#4682b4",
    "slategray": "#708090",
    "beige": "#f5f5dc",
    "ivory": "#fffff0",
    "khaki": "#f0e68c",
    "lavender": "#e6e6fa",
    "orchid": "#da70d6",
    "tomato": "#ff6347",
    "chocolate": "#d2691e",
    "crimson": "#dc143c",
    "tealblue": "#367588",
}

HEX_TO_NAME = {value: key for key, value in COLOR_MAP.items()}


def _parse_hex(value: Any) -> Tuple[str | None, str | None]:
    if value is None:
        return None, "Color is required."
    raw = str(value).strip().lstrip("#")
    if len(raw) not in {3, 6}:
        return None, "Hex must be 3 or 6 characters."
    if not all(ch in "0123456789abcdefABCDEF" for ch in raw):
        return None, "Hex must be a valid color."
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    return "#" + raw.lower(), None


def _hex_to_rgb(hex_value: str) -> Tuple[int, int, int]:
    raw = hex_value.lstrip("#")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def _distance(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def _closest_name(hex_value: str) -> str:
    rgb = _hex_to_rgb(hex_value)
    closest = None
    closest_dist = None
    for name, color_hex in COLOR_MAP.items():
        dist = _distance(rgb, _hex_to_rgb(color_hex))
        if closest_dist is None or dist < closest_dist:
            closest = name
            closest_dist = dist
    return closest or ""


def convert_color(value: Any) -> Tuple[Dict[str, str] | None, str | None]:
    if value is None:
        return None, "Color is required."
    raw = str(value).strip()
    if not raw:
        return None, "Color is required."

    if raw.startswith("#") or all(ch in "0123456789abcdefABCDEF" for ch in raw.strip("#")):
        hex_value, error = _parse_hex(raw)
        if error or hex_value is None:
            return None, error
        name = HEX_TO_NAME.get(hex_value)
        closest = _closest_name(hex_value)
        return {
            "input": raw,
            "hex": hex_value,
            "name": name or "",
            "closest_name": closest,
        }, None

    key = raw.lower().replace(" ", "")
    hex_value = COLOR_MAP.get(key)
    if not hex_value:
        return None, "Unknown color name."

    return {
        "input": raw,
        "hex": hex_value,
        "name": key,
        "closest_name": key,
    }, None
