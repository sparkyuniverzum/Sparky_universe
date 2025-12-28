from __future__ import annotations

from typing import Any, Dict, List, Tuple

from modules.sparky_core.core.rng import make_rng, parse_seed

LOREM_WORDS = [
    "lorem",
    "ipsum",
    "dolor",
    "sit",
    "amet",
    "consectetur",
    "adipiscing",
    "elit",
    "sed",
    "do",
    "eiusmod",
    "tempor",
    "incididunt",
    "ut",
    "labore",
    "et",
    "dolore",
    "magna",
    "aliqua",
    "ut",
    "enim",
    "ad",
    "minim",
    "veniam",
    "quis",
    "nostrud",
    "exercitation",
    "ullamco",
    "laboris",
    "nisi",
    "ut",
    "aliquip",
    "ex",
    "ea",
    "commodo",
    "consequat",
    "duis",
    "aute",
    "irure",
    "dolor",
    "in",
    "reprehenderit",
    "in",
    "voluptate",
    "velit",
    "esse",
    "cillum",
    "dolore",
    "eu",
    "fugiat",
    "nulla",
    "pariatur",
    "excepteur",
    "sint",
    "occaecat",
    "cupidatat",
    "non",
    "proident",
    "sunt",
    "in",
    "culpa",
    "qui",
    "officia",
    "deserunt",
    "mollit",
    "anim",
    "id",
    "est",
    "laborum",
]

MAX_PARAGRAPHS = 20
MAX_WORDS = 200


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


def _sentence(words: List[str]) -> str:
    if not words:
        return ""
    text = " ".join(words)
    return text[0].upper() + text[1:] + "."


def generate_lorem(
    paragraphs: Any,
    words_per_paragraph: Any,
    *,
    start_with_lorem: bool = True,
    seed: Any = None,
) -> Tuple[Dict[str, List[str]] | None, str | None]:
    para_int, error = _parse_int(paragraphs, label="Paragraphs", default=3)
    if error or para_int is None:
        return None, error

    words_int, error = _parse_int(words_per_paragraph, label="Words", default=60)
    if error or words_int is None:
        return None, error

    if para_int <= 0 or para_int > MAX_PARAGRAPHS:
        return None, f"Paragraphs must be between 1 and {MAX_PARAGRAPHS}."
    if words_int <= 0 or words_int > MAX_WORDS:
        return None, f"Words must be between 1 and {MAX_WORDS}."

    seed_int, error = parse_seed(seed)
    if error:
        return None, error
    rng = make_rng(seed_int)
    values: List[str] = []

    for index in range(para_int):
        words = [rng.choice(LOREM_WORDS) for _ in range(words_int)]
        if start_with_lorem and index == 0:
            base = ["lorem", "ipsum", "dolor", "sit", "amet"]
            if words_int >= len(base):
                words[: len(base)] = base
        paragraph = _sentence(words)
        values.append(paragraph)

    return {
        "paragraphs": para_int,
        "words": words_int,
        "seed": seed_int,
        "values": values,
    }, None
