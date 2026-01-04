#!/usr/bin/env python3
from __future__ import annotations

from universe.holiday_digest import run_holiday_digest


def main() -> None:
    results = run_holiday_digest()
    print(
        "Holiday digest",
        f"checked={results['checked']}",
        f"sent={results['sent']}",
        f"failed={results['failed']}",
    )


if __name__ == "__main__":
    main()
