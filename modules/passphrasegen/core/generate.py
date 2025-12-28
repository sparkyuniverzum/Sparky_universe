from __future__ import annotations

import secrets
from typing import Any, Dict, List, Tuple

WORDS = [
    "anchor", "april", "atlas", "autumn", "beacon", "breeze", "bright", "canyon",
    "canvas", "cello", "charm", "cinder", "cloud", "cobalt", "comet", "copper",
    "crane", "crisp", "dawn", "delta", "drift", "ember", "ember", "fable",
    "feather", "fennel", "field", "flint", "forest", "frost", "garden", "glade",
    "glow", "grain", "harbor", "honey", "horizon", "jade", "june", "lattice",
    "leaf", "lumen", "maple", "meadow", "midnight", "mist", "monarch", "moon",
    "moss", "nebula", "nectar", "oasis", "olive", "opal", "orbit", "orchid",
    "pearl", "pioneer", "plume", "prairie", "quartz", "quiet", "raven", "river",
    "rover", "sable", "saffron", "sage", "sequoia", "shadow", "signal", "silver",
    "sky", "solace", "solar", "spectrum", "spring", "stone", "sunset", "summit",
    "tide", "timber", "trail", "tranquil", "twilight", "vector", "velvet", "verdant",
    "vivid", "wander", "whisper", "wild", "willow", "winter", "zenith", "zephyr",
    "amber", "arcade", "aurora", "basil", "bloom", "brisk", "cascade", "citron",
    "clover", "cosmic", "creek", "daisy", "dune", "echo", "emberly", "evergreen",
    "fresco", "glimmer", "granite", "harvest", "island", "jubilant", "lagoon",
    "lantern", "lilac", "marble", "mirage", "morning", "nylon", "oracle", "pixel",
    "plasma", "quiver", "radial", "ripple", "sierra", "sonic", "stellar", "terra",
]

MAX_COUNT = 200
MAX_WORDS = 8
MAX_SEPARATOR = 4
CAPS_OPTIONS = {"lower", "upper", "title"}


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


def _parse_separator(value: Any) -> Tuple[str | None, str | None]:
    if value is None:
        return "-", None
    raw = str(value)
    if raw == "":
        return "-", None
    if raw.strip() == "":
        sep = " "
    else:
        key = raw.strip()
        if key.lower() == "none":
            sep = ""
        elif key.lower() == "space":
            sep = " "
        else:
            sep = key
    if len(sep) > MAX_SEPARATOR:
        return None, f"Separator must be {MAX_SEPARATOR} characters or less."
    return sep, None


def _parse_caps(value: Any) -> Tuple[str | None, str | None]:
    if value is None:
        return "lower", None
    raw = str(value).strip().lower()
    if not raw:
        return "lower", None
    if raw not in CAPS_OPTIONS:
        return None, "Caps must be lower, upper, or title."
    return raw, None


def _apply_caps(word: str, mode: str) -> str:
    if mode == "upper":
        return word.upper()
    if mode == "title":
        return word.title()
    return word.lower()


def generate_passphrases(
    words: Any,
    count: Any,
    *,
    separator: Any = "-",
    caps: Any = "lower",
) -> Tuple[Dict[str, List[str]] | None, str | None]:
    words_int, error = _parse_int(words, label="Words", default=4)
    if error or words_int is None:
        return None, error

    count_int, error = _parse_int(count, label="Count", default=5)
    if error or count_int is None:
        return None, error

    if words_int <= 0 or words_int > MAX_WORDS:
        return None, f"Words must be between 1 and {MAX_WORDS}."
    if count_int <= 0 or count_int > MAX_COUNT:
        return None, f"Count must be between 1 and {MAX_COUNT}."

    separator_value, error = _parse_separator(separator)
    if error or separator_value is None:
        return None, error

    caps_value, error = _parse_caps(caps)
    if error or caps_value is None:
        return None, error

    phrases: List[str] = []
    for _ in range(count_int):
        parts = [_apply_caps(secrets.choice(WORDS), caps_value) for _ in range(words_int)]
        phrases.append(separator_value.join(parts))

    return {
        "count": count_int,
        "words": words_int,
        "separator": separator_value,
        "caps": caps_value,
        "values": phrases,
    }, None
