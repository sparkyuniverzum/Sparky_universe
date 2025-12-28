from __future__ import annotations

from typing import Any, Dict, List, Tuple


MAX_STEPS = 12


def _parse_int(value: Any, *, label: str, default: int | None = None) -> Tuple[int | None, str | None]:
    if value is None or str(value).strip() == "":
        if default is None:
            return None, f"{label} is required."
        return default, None
    raw = str(value).strip()
    try:
        number = int(raw)
    except ValueError:
        return None, f"{label} must be a whole number."
    return number, None


def _parse_hex(value: Any) -> Tuple[str | None, str | None]:
    if value is None:
        return None, "Hex color is required."
    raw = str(value).strip().lstrip("#")
    if len(raw) not in {3, 6}:
        return None, "Hex must be 3 or 6 characters."
    if not all(ch in "0123456789abcdefABCDEF" for ch in raw):
        return None, "Hex must be a valid color."
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    return raw.lower(), None


def _hex_to_rgb(hex_value: str) -> Tuple[int, int, int]:
    return int(hex_value[0:2], 16), int(hex_value[2:4], 16), int(hex_value[4:6], 16)


def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#" + "".join(f"{max(0, min(255, c)):02x}" for c in rgb)


def _mix_channel(base: int, target: int, ratio: float) -> int:
    return round(base + (target - base) * ratio)


def generate_palette(
    base_hex: Any,
    steps: Any,
    *,
    mode: str = "tints",
) -> Tuple[Dict[str, List[str]] | None, str | None]:
    hex_value, error = _parse_hex(base_hex)
    if error or hex_value is None:
        return None, error

    steps_int, error = _parse_int(steps, label="Steps", default=6)
    if error or steps_int is None:
        return None, error

    if steps_int <= 1 or steps_int > MAX_STEPS:
        return None, f"Steps must be between 2 and {MAX_STEPS}."

    mode_key = mode.lower().strip()
    if mode_key not in {"tints", "shades", "both"}:
        return None, "Mode must be tints, shades, or both."

    base_rgb = _hex_to_rgb(hex_value)
    palette: List[str] = []

    if mode_key in {"tints", "both"}:
        for i in range(steps_int):
            ratio = (i + 1) / (steps_int + 1)
            mixed = tuple(_mix_channel(c, 255, ratio) for c in base_rgb)
            palette.append(_rgb_to_hex(mixed))

    if mode_key in {"shades", "both"}:
        for i in range(steps_int):
            ratio = (i + 1) / (steps_int + 1)
            mixed = tuple(_mix_channel(c, 0, ratio) for c in base_rgb)
            palette.append(_rgb_to_hex(mixed))

    return {
        "base": f"#{hex_value}",
        "mode": mode_key,
        "steps": steps_int,
        "colors": palette,
    }, None
