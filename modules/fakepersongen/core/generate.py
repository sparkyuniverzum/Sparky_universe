from __future__ import annotations

from typing import Any, Dict, List, Tuple

from modules.sparky_core.core.rng import make_rng, parse_seed

FIRST_NAMES = [
    "Alex", "Anna", "Ben", "Cleo", "Daniel", "Eva", "Filip", "Grace", "Hana",
    "Ian", "Julia", "Karel", "Lena", "Marek", "Nora", "Owen", "Petra", "Quinn",
    "Roman", "Sara", "Tomas", "Uma", "Viktor", "Wendy", "Xenia", "Yara", "Zdenek",
]

LAST_NAMES = [
    "Novak", "Svoboda", "Dvorak", "Novotny", "Cerny", "Prochazka", "Kucera",
    "Kovar", "Horak", "Nemecek", "Pokorny", "Hajek", "Jelinek", "Kratochvil",
    "Bartos", "Simek", "Urban", "Vesely", "Fiala", "Soukup",
]

STREETS = [
    "Maple", "Oak", "Cedar", "Pine", "Elm", "River", "Hill", "Sunset", "Lake", "Garden",
]

CITIES = ["Prague", "Brno", "Ostrava", "Plzen", "Liberec", "Olomouc", "Hradec Kralove"]

DOMAINS = ["example.com", "mail.test", "demo.local"]

MAX_COUNT = 200


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


def _email_for(first: str, last: str, domain: str) -> str:
    user = f"{first}.{last}".lower().replace(" ", ".")
    return f"{user}@{domain}"


def generate_people(
    count: Any,
    *,
    seed: Any = None,
) -> Tuple[Dict[str, List[Dict[str, str]]] | None, str | None]:
    count_int, error = _parse_int(count, label="Count", default=5)
    if error or count_int is None:
        return None, error

    if count_int <= 0 or count_int > MAX_COUNT:
        return None, f"Count must be between 1 and {MAX_COUNT}."

    seed_int, error = parse_seed(seed)
    if error:
        return None, error
    rng = make_rng(seed_int)
    people: List[Dict[str, str]] = []

    for _ in range(count_int):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        street = rng.choice(STREETS)
        number = rng.randint(1, 220)
        city = rng.choice(CITIES)
        domain = rng.choice(DOMAINS)

        person = {
            "name": f"{first} {last}",
            "email": _email_for(first, last, domain),
            "phone": f"+420 {rng.randint(600, 799)} {rng.randint(100, 999)} {rng.randint(100, 999)}",
            "address": f"{street} {number}, {city}",
        }
        people.append(person)

    return {"count": count_int, "seed": seed_int, "people": people}, None
