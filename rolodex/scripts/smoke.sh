#!/usr/bin/env bash
# smoke.sh — hit /v1/models and one chat completion against a running rolodex.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

: "${ROLODEX_PORT:=4000}"
: "${ROLODEX_MASTER_KEY:=sk-rolodex}"
LANE="${1:-lane/local}"
BASE="http://127.0.0.1:${ROLODEX_PORT}"

echo "== GET ${BASE}/v1/models =="
curl -fsS "${BASE}/v1/models" -H "Authorization: Bearer ${ROLODEX_MASTER_KEY}" | python3 -m json.tool | head -80

echo
echo "== POST chat lane=${LANE} =="
curl -fsS "${BASE}/v1/chat/completions" \
  -H "Authorization: Bearer ${ROLODEX_MASTER_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json,sys; print(json.dumps({'model':sys.argv[1],'messages':[{'role':'user','content':'Reply with exactly: pong'}],'max_tokens':32,'temperature':0}))" "$LANE")" \
  | python3 -m json.tool

echo
echo "SMOKE OK"
