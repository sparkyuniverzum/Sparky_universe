#!/usr/bin/env python3
from __future__ import annotations

from universe.monitoring import run_watchers


def main() -> None:
    results = run_watchers()
    print(
        "Watchers check",
        f"checked={results['checked']}",
        f"triggered={results['triggered']}",
        f"sent={results['sent']}",
        f"failed={results['failed']}",
    )


if __name__ == "__main__":
    main()
