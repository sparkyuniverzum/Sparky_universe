#!/usr/bin/env bash
set -euo pipefail

host="${SPARKY_HOST:-0.0.0.0}"
port="${PORT:-8000}"
python_bin="python"

if [[ -x ".venv/bin/python" ]]; then
  python_bin=".venv/bin/python"
fi

if [[ "${SPARKY_LOAD_DOTENV:-on}" != "off" ]]; then
  dotenv_path="${SPARKY_DOTENV_PATH:-}"
  if [[ -n "${dotenv_path}" ]]; then
    if [[ -f "${dotenv_path}" ]]; then
      set -a
      # shellcheck disable=SC1091
      source "${dotenv_path}"
      set +a
    fi
  elif [[ -f ".env.local" ]]; then
    set -a
    # shellcheck disable=SC1091
    source ".env.local"
    set +a
  elif [[ -f ".env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source ".env"
    set +a
  fi
fi

if [[ -n "${SPARKY_MODULE:-}" ]]; then
  exec "${python_bin}" -m uvicorn "modules.${SPARKY_MODULE}.tool.app:app" --host "${host}" --port "${port}"
fi

exec "${python_bin}" -m uvicorn "universe.app:app" --host "${host}" --port "${port}"
