from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Tuple


ALLOWED_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Constant,
}


def _safe_eval(expr: str) -> float:
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_NODES:
            raise ValueError("Unsupported expression")
    return float(eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}))


def _parse_values(text: str | None) -> Dict[str, float]:
    values: Dict[str, float] = {}
    if not text:
        return values
    for line in text.replace("\r", "").split("\n"):
        if not line.strip() or "=" not in line:
            continue
        name, raw = line.split("=", 1)
        key = name.strip()
        if not key:
            continue
        try:
            values[key] = float(raw.strip())
        except ValueError:
            continue
    return values


def _extract_variables(expr: str) -> List[str]:
    tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9_]*\b", expr)
    return list(dict.fromkeys(tokens))


def build_steps(
    formula: str | None, values_text: str | None
) -> Tuple[Dict[str, Any] | None, str | None]:
    if formula is None or not str(formula).strip():
        return None, "Formula is required."

    raw = str(formula).strip()
    left = ""
    expr = raw
    if "=" in raw:
        left, expr = [part.strip() for part in raw.split("=", 1)]

    if not expr:
        return None, "Formula is required."

    values = _parse_values(values_text)
    variables = _extract_variables(expr)

    substituted = expr
    for name, value in values.items():
        substituted = re.sub(rf"\b{re.escape(name)}\b", str(value), substituted)

    steps: List[str] = []
    if left:
        steps.append(f"Solve for {left} using: {expr}")
    else:
        steps.append(f"Use the formula: {expr}")

    missing = [name for name in variables if name not in values]
    if values:
        steps.append(f"Substitute values: {substituted}")

    result_value: float | None = None
    if not missing:
        try:
            result_value = _safe_eval(substituted)
            steps.append(f"Compute result: {result_value}")
        except ValueError:
            steps.append("Compute result: (unsupported expression)")

    return {
        "variables": variables,
        "missing_values": missing,
        "steps": steps,
        "result": result_value,
    }, None
