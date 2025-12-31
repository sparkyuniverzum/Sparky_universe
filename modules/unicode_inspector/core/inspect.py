from __future__ import annotations

import unicodedata
from typing import Dict, List, Tuple


ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0xFEFF}
SPECIALS = {0x00A0, 0x00AD}
MAX_ISSUES = 100


def _codepoint_label(code: int) -> str:
    return f"U+{code:04X}"


def _is_control(ch: str) -> bool:
    if ch in {"\n", "\r", "\t"}:
        return False
    return unicodedata.category(ch).startswith("C")


def inspect_text(
    text: str | None,
    *,
    normalization: str = "none",
) -> Tuple[Dict[str, object] | None, str | None]:
    if text is None or not text.strip():
        return None, "Text is required."

    norm_key = normalization.strip().upper()
    if norm_key not in {"NONE", "NFC", "NFD", "NFKC", "NFKD"}:
        return None, "Normalization must be none, NFC, NFD, NFKC, or NFKD."

    issues: List[Dict[str, object]] = []
    non_ascii = 0
    control_count = 0
    zero_width_count = 0
    special_count = 0

    for idx, ch in enumerate(text):
        code = ord(ch)
        if code > 127:
            non_ascii += 1
        if _is_control(ch):
            control_count += 1
            if len(issues) < MAX_ISSUES:
                issues.append(
                    {
                        "index": idx + 1,
                        "type": "control",
                        "codepoint": _codepoint_label(code),
                        "category": unicodedata.category(ch),
                        "name": unicodedata.name(ch, "UNKNOWN"),
                    }
                )
            continue
        if code in ZERO_WIDTH:
            zero_width_count += 1
            if len(issues) < MAX_ISSUES:
                issues.append(
                    {
                        "index": idx + 1,
                        "type": "zero_width",
                        "codepoint": _codepoint_label(code),
                        "category": unicodedata.category(ch),
                        "name": unicodedata.name(ch, "UNKNOWN"),
                    }
                )
            continue
        if code in SPECIALS:
            special_count += 1
            if len(issues) < MAX_ISSUES:
                issues.append(
                    {
                        "index": idx + 1,
                        "type": "special_space",
                        "codepoint": _codepoint_label(code),
                        "category": unicodedata.category(ch),
                        "name": unicodedata.name(ch, "UNKNOWN"),
                    }
                )

    normalized = text
    if norm_key != "NONE":
        normalized = unicodedata.normalize(norm_key, text)

    return {
        "length": len(text),
        "non_ascii": non_ascii,
        "control_chars": control_count,
        "zero_width": zero_width_count,
        "special_spaces": special_count,
        "issues": issues,
        "issues_truncated": len(issues) >= MAX_ISSUES,
        "normalized": normalized if norm_key != "NONE" else None,
        "normalization": norm_key.lower(),
    }, None
