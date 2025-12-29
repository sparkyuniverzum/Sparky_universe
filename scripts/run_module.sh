#!/usr/bin/env bash
set -euo pipefail

host="${SPARKY_HOST:-0.0.0.0}"
port="${PORT:-8000}"
python_bin="python"

if [[ -x ".venv/bin/python" ]]; then
  python_bin=".venv/bin/python"
fi

if [[ -n "${SPARKY_MODULE:-}" ]]; then
  exec "${python_bin}" -m uvicorn "modules.${SPARKY_MODULE}.tool.app:app" --host "${host}" --port "${port}"
fi

exec "${python_bin}" -m uvicorn "universe.app:app" --host "${host}" --port "${port}"
