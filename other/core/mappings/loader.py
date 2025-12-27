from importlib import import_module
from typing import Sequence


def register_all() -> int:
    """
    Dynamicky načte všechny mapper moduly a vrátí jejich počet.
    Použití: startovací log v app/main.py.
    """
    modules: Sequence[str] = (
        "app.core.mappings.products",
        "app.core.mappings.suppliers",
        "app.core.mappings.receipts",
    )
    for path in modules:
        import_module(path)
    return len(modules)
