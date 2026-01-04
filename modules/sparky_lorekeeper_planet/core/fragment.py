from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class Fragment:
    key: str
    label: str
    title: str
    subtitle: str
    text: str


FRAGMENT_SOURCES = {
    "collapse": {
        "label": "Collapse",
        "file": "ENTRY_002_COLLAPSE_EN.md",
    },
    "signal": {
        "label": "Signal",
        "file": "ENTRY_003_SIGNAL_EN.md",
    },
}

TONES = {
    "mystic": "The archive speaks in silence.",
    "human": "A small human thread holds.",
    "cold": "Record sealed. Signal persists.",
}

_CACHE: Dict[str, Fragment] = {}


def list_fragments() -> List[Dict[str, str]]:
    return [{"key": key, "label": data["label"]} for key, data in FRAGMENT_SOURCES.items()]


def tone_options() -> List[Dict[str, str]]:
    return [{"key": key, "label": label.title()} for key, label in TONES.items()]


def resolve_tone(key: str) -> str:
    return TONES.get(key, TONES["mystic"])


def _root_dir() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "brand" / "Story" / "entries").exists():
            return parent
    return current.parents[3]


def _parse_entry(raw: str) -> Dict[str, str]:
    lines = [line.rstrip() for line in raw.splitlines()]
    content_lines = [line for line in lines if line.strip()]
    title = content_lines[0] if content_lines else "ENTRY"
    subtitle = content_lines[1] if len(content_lines) > 1 else ""
    body_start = lines.index(content_lines[1]) + 1 if len(content_lines) > 1 else 0
    body_lines = lines[body_start:]

    paragraphs: List[str] = []
    current: List[str] = []
    for line in body_lines:
        if not line.strip():
            if current:
                paragraphs.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append("\n".join(current))

    text = "\n\n".join(paragraphs).strip()
    return {"title": title, "subtitle": subtitle, "text": text}


def load_fragment(key: str) -> Fragment | None:
    if key in _CACHE:
        return _CACHE[key]

    data = FRAGMENT_SOURCES.get(key)
    if not data:
        return None

    entries_dir = _root_dir() / "brand" / "Story" / "entries"
    entry_path = entries_dir / data["file"]
    if not entry_path.exists():
        return None

    raw = entry_path.read_text(encoding="utf-8")
    parsed = _parse_entry(raw)
    fragment = Fragment(
        key=key,
        label=data["label"],
        title=parsed["title"],
        subtitle=parsed["subtitle"],
        text=parsed["text"],
    )
    _CACHE[key] = fragment
    return fragment
