from __future__ import annotations

from typing import Any, Dict, List, Tuple

TYPE_EXAMPLES: Dict[str, Any] = {
    "string": "string",
    "text": "text",
    "int": 0,
    "integer": 0,
    "float": 0.0,
    "number": 0.0,
    "bool": False,
    "boolean": False,
    "date": "2024-01-01",
    "datetime": "2024-01-01T00:00:00Z",
    "email": "user@example.com",
    "url": "https://example.com",
    "object": {},
    "array": [],
}


def _split_lines(value: str | None) -> List[str]:
    if not value:
        return []
    lines: List[str] = []
    cleaned = value.replace("\r", "")
    for line in cleaned.split("\n"):
        item = line.strip()
        if item:
            lines.append(item)
    return lines


def _parse_field(line: str) -> Tuple[str, str]:
    if ":" in line:
        name, type_hint = line.split(":", 1)
        return name.strip(), type_hint.strip()
    return line.strip(), "string"


def _value_for(type_hint: str) -> Any:
    hint = type_hint.strip()
    if hint.endswith("[]"):
        base = hint[:-2].strip()
        value = TYPE_EXAMPLES.get(base, "string")
        return [value]
    return TYPE_EXAMPLES.get(hint, "string")


def _assign_path(root: Dict[str, Any], path: List[str], value: Any) -> None:
    current = root
    for part in path[:-1]:
        existing = current.get(part)
        if not isinstance(existing, dict):
            current[part] = {}
        current = current[part]
    current[path[-1]] = value


def generate_json_template(
    *,
    fields_text: str | None,
) -> Tuple[Dict[str, Any] | None, str | None]:
    lines = _split_lines(fields_text)
    if not lines:
        return None, "Provide at least one field."
    if len(lines) > 500:
        return None, "Limit is 500 fields."

    template: Dict[str, Any] = {}
    for line in lines:
        name, type_hint = _parse_field(line)
        if not name:
            continue
        path = [part for part in name.split(".") if part]
        if not path:
            continue
        value = _value_for(type_hint)
        _assign_path(template, path, value)

    if not template:
        return None, "No valid fields found."

    return {
        "fields": len(lines),
        "template": template,
    }, None
