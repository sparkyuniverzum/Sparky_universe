from __future__ import annotations

from typing import Iterable
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.catalog.repositories.category_repository import ProductCategoryRepository

_KEYWORDS: dict[str, list[str]] = {
    "elektro": [
        "kabel",
        "adapter",
        "nabije",
        "nabíje",
        "usb",
        "hdmi",
        "bater",
        "powerbank",
        "svitiln",
        "svítiln",
        "lamp",
        "projektor",
        "konzol",
        "dock",
        "dokovac",
        "hub",
        "magnet",
        "magsafe",
        "drzak",
        "držák",
        "telefon",
        "mobil",
        "herni",
        "žehlič",
        "zehlick",
    ],
    "obleceni": [
        "tricko",
        "tričko",
        "triko",
        "top ",
        "halen",
        "bluza",
        "blůza",
        "kosile",
        "košile",
        "sat",
        "šat",
        "sukn",
        "kalhot",
        "legin",
        "legín",
        "kraťas",
        "kratasy",
        "kratasky",
        "mikina",
        "bunda",
        "kabat",
        "kabát",
        "svetr",
        "cardigan",
        "vesta",
        "overal",
        "kostym",
        "kostým",
        "pyzam",
        "pyžam",
        "plavk",
        "ponoz",
        "ponož",
        "puncoch",
        "punčo",
        "sal ",
        "šál",
        "satek",
        "šátek",
        "cepice",
        "čepice",
        "ksiltov",
        "kšiltov",
        "rukavic",
        "boty",
        "bot ",
        "bot.",
        "tenisk",
        "pantof",
        "sandál",
        "sandal",
        "lodič",
        "lodic",
        "sortk",
        "šortk",
    ],
    "hracky": [
        "hračka",
        "hracka",
        "hra ",
        "hra-",
        "puzzle",
        "lego",
        "kostka",
        "stavebnice",
        "panenka",
        "figur",
        "plys",
        "plyš",
        "auticko",
        "autíčko",
        "domecek",
        "domeček",
    ],
    "doplnky": [
        "doplnek",
        "doplněk",
        "batoh",
        "taška",
        "taska",
        "kabelk",
        "psanick",
        "penezenka",
        "peněženka",
        "pasek",
        "pásek",
        "nahrdelnik",
        "náhrdelník",
        "naramek",
        "náramek",
        "nausnic",
        "naušnic",
        "nausnice",
        "náušnice",
        "prsten",
        "retizek",
        "řetízek",
        "broz",
        "brož",
        "spona",
        "perla",
        "spiral",
        "klobouk",
        "helma",
        "helmet",
        "motork",
        "satek",
        "šátek",
        "sal ",
        "šál",
        "rucnik",
        "ručník",
    ],
    "hobby": [
        "nastroj",
        "nástroj",
        "sklo",
        "keram",
        "dekor",
        "svicka",
        "svíčka",
        "ramec",
        "rámeč",
        "zahrad",
        "gril",
        "naradi",
        "nářadí",
        "zaves",
        "závěs",
    ],
}

SEED_CATEGORIES = [
    ("hobby", "Hobby"),
    ("elektro", "Elektro"),
    ("obleceni", "Oblečení"),
    ("hracky", "Hračky"),
    ("doplnky", "Doplňky"),
]

_seed_applied = False


def _contains_keyword(text: str, keywords: Iterable[str]) -> bool:
    lower = text.lower()
    return any(k in lower for k in keywords)


def classify_product_category(name: str | None, supplier_sku: str | None = None, supplier_id: str | None = None) -> str | None:
    source_texts = [t for t in (name, supplier_sku, supplier_id) if t]
    if not source_texts:
        return None
    text = " ".join(source_texts)
    for code, keywords in _KEYWORDS.items():
        if _contains_keyword(text, keywords):
            return code
    return None


async def ensure_seed_categories(db: AsyncSession) -> None:
    global _seed_applied
    if _seed_applied:
        return
    repo = ProductCategoryRepository(db)
    await repo.create_many_if_missing(SEED_CATEGORIES)
    _seed_applied = True


__all__ = ["classify_product_category", "ensure_seed_categories", "SEED_CATEGORIES"]
