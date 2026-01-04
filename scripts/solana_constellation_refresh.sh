#!/usr/bin/env bash
set -euo pipefail

base_url="${SPARKY_PUBLIC_BASE_URL:-http://127.0.0.1:8000}"
endpoint="${base_url%/}/planet/solana/api/refresh"

headers=()
if [[ -n "${SPARKY_SOLANA_REFRESH_TOKEN:-}" ]]; then
  headers+=("-H" "x-constellation-token: ${SPARKY_SOLANA_REFRESH_TOKEN}")
fi

curl -sS -X POST "${endpoint}" "${headers[@]}"
