#!/usr/bin/env bash
set -euo pipefail

host="${SPARKY_HOST:-0.0.0.0}"
port="${PORT:-8000}"

if [[ -n "${SPARKY_MODULE:-}" ]]; then
  exec python -m uvicorn "modules.${SPARKY_MODULE}.tool.app:app" --host "${host}" --port "${port}"
fi

exec python -m uvicorn "universe.app:app" --host "${host}" --port "${port}"
