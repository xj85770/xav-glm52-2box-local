#!/usr/bin/env bash
# start.sh — lanes agent dashboard (expects lanes2 on :4000, or set LANES2_BASE)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
cd "$ROOT"

export PATH="${HOME}/.local/bin:${PATH}"
export LANES_PORT="${LANES_PORT:-3000}"
export LANES2_BASE="${LANES2_BASE:-http://127.0.0.1:4000}"
export LANES2_MASTER_KEY="${LANES2_MASTER_KEY:-sk-lanes2}"
export LANES_DEFAULT_MODEL="${LANES_DEFAULT_MODEL:-lane/smart}"

if [[ -f "$REPO/lanes2/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO/lanes2/.env"
  set +a
  export LANES2_MASTER_KEY="${LANES2_MASTER_KEY:-sk-lanes2}"
  export LANES2_BASE="${LANES2_BASE:-http://127.0.0.1:${LANES2_PORT:-4000}}"
fi

echo "lanes dashboard → http://127.0.0.1:${LANES_PORT}"
echo "lanes2 backend  → ${LANES2_BASE}"
echo "default model   → ${LANES_DEFAULT_MODEL}"

if ! curl -fsS "${LANES2_BASE}/health" >/dev/null 2>&1; then
  echo "WARNING: lanes2 not reachable at ${LANES2_BASE}"
  echo "Start it with:  ./scripts/start-stack.sh   (or lanes2/scripts/start.sh)"
fi

exec python3 -m uvicorn app:create_app --factory --host 127.0.0.1 --port "$LANES_PORT" --app-dir "$ROOT"
