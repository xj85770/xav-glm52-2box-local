#!/usr/bin/env bash
# smoke.sh — list models/lanes, then hit one chat completion.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

: "${LANES2_PORT:=4000}"
: "${LANES2_MASTER_KEY:=sk-lanes2}"
LANE="${1:-lanes}"
BASE="http://127.0.0.1:${LANES2_PORT}"

echo "== GET ${BASE}/v1/lanes =="
curl -fsS "${BASE}/v1/lanes" -H "Authorization: Bearer ${LANES2_MASTER_KEY}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); 
[print(f\"{k}: {v['ready_count']}/{v['card_count']} ready → {', '.join(v['ready_ids'][:6])}{'…' if len(v['ready_ids'])>6 else ''}\") for k,v in d['lanes'].items()]"

echo
echo "== GET ${BASE}/v1/models (lanes + individual APIs) =="
curl -fsS "${BASE}/v1/models" -H "Authorization: Bearer ${LANES2_MASTER_KEY}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); 
kinds={};
[kinds.__setitem__(x.get('kind','?'), kinds.get(x.get('kind','?'),0)+1) for x in d['data']];
print('counts', kinds);
print('sample ids:', ', '.join(x['id'] for x in d['data'][:12]), '…')"

echo
echo "== POST chat model=${LANE} =="
curl -fsS "${BASE}/v1/chat/completions" \
  -H "Authorization: Bearer ${LANES2_MASTER_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json,sys; print(json.dumps({'model':sys.argv[1],'messages':[{'role':'user','content':'Reply with exactly: pong'}],'max_tokens':64,'temperature':0}))" "$LANE")" \
  | python3 -m json.tool | head -80

echo
echo "SMOKE OK"
