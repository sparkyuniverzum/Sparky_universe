from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


def _split_sentences(text: str) -> List[str]:
    cleaned = text.replace("\r", " ").strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def _extract_pairs(sentences: List[str], limit: int) -> List[Dict[str, str]]:
    patterns = [
        re.compile(r"^(.+?)\s+is\s+(.+)$", re.IGNORECASE),
        re.compile(r"^(.+?)\s+are\s+(.+)$", re.IGNORECASE),
        re.compile(r"^(.+?)\s+means\s+(.+)$", re.IGNORECASE),
        re.compile(r"^(.+?)\s+refers to\s+(.+)$", re.IGNORECASE),
    ]
    pairs: List[Dict[str, str]] = []
    for sentence in sentences:
        trimmed = sentence.strip(" .")
        for pattern in patterns:
            match = pattern.match(trimmed)
            if match:
                subject = match.group(1).strip()
                answer = match.group(2).strip()
                if subject and len(subject) < 120:
                    pairs.append({"question": f"What is {subject}?", "answer": answer})
                    break
        if len(pairs) >= limit:
            return pairs
    return pairs


def _extract_terms(text: str) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-']{3,}", text.lower())
    return list(dict.fromkeys(words))


def build_recall_prompts(
    text: str | None, limit: int
) -> Tuple[Dict[str, Any] | None, str | None]:
    if text is None or not str(text).strip():
        return None, "Text is required."
    if limit <= 0 or limit > 20:
        return None, "Limit must be between 1 and 20."

    text_value = str(text)
    sentences = _split_sentences(text_value)
    if not sentences:
        return None, "Text is required."

    pairs = _extract_pairs(sentences, limit)
    if len(pairs) < limit:
        terms = _extract_terms(text_value)
        for term in terms:
            if len(pairs) >= limit:
                break
            question = f"Explain {term}."
            if any(pair["question"] == question for pair in pairs):
                continue
            answer = ""
            for sentence in sentences:
                if re.search(rf"\b{re.escape(term)}\b", sentence, re.IGNORECASE):
                    answer = sentence
                    break
            pairs.append({"question": question, "answer": answer})

    return {
        "count": len(pairs),
        "pairs": pairs[:limit],
    }, None
