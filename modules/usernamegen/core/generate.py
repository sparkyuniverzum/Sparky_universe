from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from modules.sparky_core.core.rng import make_rng, parse_seed

ADJECTIVES = [
    "bright",
    "calm",
    "clever",
    "cosmic",
    "crisp",
    "daring",
    "dusty",
    "ember",
    "fleet",
    "glossy",
    "golden",
    "lunar",
    "mellow",
    "midnight",
    "neon",
    "nimble",
    "nova",
    "quiet",
    "rapid",
    "rising",
    "rustic",
    "silent",
    "silver",
    "solar",
    "steady",
    "swift",
    "vivid",
    "wild",
    "wise",
    "zen",
    "cobalt",
    "stellar",
]

NOUNS = [
    "atlas",
    "beacon",
    "breeze",
    "canyon",
    "comet",
    "drift",
    "echo",
    "falcon",
    "forge",
    "harbor",
    "horizon",
    "ion",
    "lagoon",
    "lumen",
    "meteor",
    "nexus",
    "orbit",
    "outpost",
    "pilot",
    "pioneer",
    "pixel",
    "quartz",
    "ridge",
    "signal",
    "spark",
    "station",
    "summit",
    "terra",
    "vector",
    "zenith",
    "raven",
    "voyager",
]

MAX_COUNT = 200
MAX_NUMBER_DIGITS = 4
MAX_SEPARATOR_LEN = 3

RE_SPACE = re.compile(r"\s+")


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
    sep = str(value)
    sep = sep.strip()
    if sep.lower() == "none":
        sep = ""
    if len(sep) > MAX_SEPARATOR_LEN:
        return None, f"Separator must be {MAX_SEPARATOR_LEN} characters or less."
    if any(ch.isspace() for ch in sep):
        sep = "".join(ch for ch in sep if not ch.isspace())
    return sep, None


def _sanitize_base(value: Any, *, separator: str, lowercase: bool) -> str:
    if value is None:
        return ""
    raw = str(value).strip()
    if not raw:
        return ""
    if lowercase:
        raw = raw.lower()
    if separator:
        raw = RE_SPACE.sub(separator, raw)
        allowed = re.escape(separator)
        raw = re.sub(rf"[^a-zA-Z0-9{allowed}]+", "", raw)
        raw = re.sub(rf"{allowed}+", separator, raw).strip(separator)
    else:
        raw = RE_SPACE.sub("", raw)
        raw = re.sub(r"[^a-zA-Z0-9]+", "", raw)
    return raw


def _format_word(word: str, *, lowercase: bool) -> str:
    return word.lower() if lowercase else word.title()


def _estimate_space(
    *,
    use_adjective: bool,
    use_noun: bool,
    include_number: bool,
    number_digits: int | None,
) -> int:
    space = 1
    if use_adjective:
        space *= len(ADJECTIVES)
    if use_noun:
        space *= len(NOUNS)
    if include_number and number_digits:
        space *= 10 ** number_digits
    return space


def generate_usernames(
    base: Any,
    count: Any,
    *,
    include_adjective: bool = True,
    include_noun: bool = True,
    include_number: bool = False,
    number_digits: Any = None,
    separator: Any = "-",
    lowercase: bool = True,
    unique: bool = False,
    seed: Any = None,
) -> Tuple[Dict[str, List[str]] | None, str | None]:
    count_int, error = _parse_int(count, label="Count", default=10)
    if error or count_int is None:
        return None, error

    if count_int <= 0 or count_int > MAX_COUNT:
        return None, f"Count must be between 1 and {MAX_COUNT}."

    sep, error = _parse_separator(separator)
    if error or sep is None:
        return None, error

    base_clean = _sanitize_base(base, separator=sep, lowercase=lowercase)
    if base is not None and str(base).strip() and not base_clean:
        return None, "Base word has no usable characters."

    if not base_clean and not include_adjective and not include_noun:
        return None, "Enable adjective or noun, or provide a base word."

    digits_int = None
    if include_number:
        digits_int, error = _parse_int(number_digits, label="Number digits", default=2)
        if error or digits_int is None:
            return None, error
        if digits_int <= 0 or digits_int > MAX_NUMBER_DIGITS:
            return None, f"Number digits must be between 1 and {MAX_NUMBER_DIGITS}."

    if unique:
        space = _estimate_space(
            use_adjective=include_adjective,
            use_noun=include_noun,
            include_number=include_number,
            number_digits=digits_int,
        )
        if count_int > space:
            return None, "Count exceeds available unique combinations."

    seed_int, error = parse_seed(seed)
    if error:
        return None, error
    rng = make_rng(seed_int)
    values: List[str] = []
    seen = set()
    max_attempts = max(count_int * 40, 200)
    attempts = 0

    while len(values) < count_int and attempts < max_attempts:
        attempts += 1
        parts: List[str] = []
        if include_adjective:
            parts.append(_format_word(rng.choice(ADJECTIVES), lowercase=lowercase))
        if base_clean:
            parts.append(base_clean)
        if include_noun:
            parts.append(_format_word(rng.choice(NOUNS), lowercase=lowercase))

        if not parts:
            break

        if sep:
            username = sep.join(parts)
        else:
            username = "".join(parts)

        if include_number and digits_int:
            number = str(rng.randrange(0, 10 ** digits_int)).zfill(digits_int)
            if sep:
                username = f"{username}{sep}{number}"
            else:
                username = f"{username}{number}"

        if unique:
            if username in seen:
                continue
            seen.add(username)
        values.append(username)

    if len(values) < count_int:
        return None, "Unable to generate enough unique usernames."

    return {
        "count": count_int,
        "separator": sep,
        "base": base_clean,
        "include_adjective": include_adjective,
        "include_noun": include_noun,
        "include_number": include_number,
        "number_digits": digits_int or 0,
        "seed": seed_int,
        "values": values,
    }, None
