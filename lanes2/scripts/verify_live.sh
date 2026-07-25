#!/usr/bin/env bash
# verify_live.sh — ship check against a running gateway (no cloud keys required).
set -euo pipefail

: "${LANES2_PORT:=4000}"
: "${LANES2_MASTER_KEY:=sk-lanes2}"
BASE="http://127.0.0.1:${LANES2_PORT}"
AUTH="Authorization: Bearer ${LANES2_MASTER_KEY}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== health =="
curl -fsS "$BASE/health" | tee "$TMP/health.json"
echo

echo "== /v1/models has lanes + individual APIs =="
curl -fsS "$BASE/v1/models" -H "$AUTH" > "$TMP/models.json"
python3 - "$TMP/models.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
ids={m["id"] for m in d["data"]}
for need in ("lanes","lane/local","lane/fast","lane/smart","lane/code","local/ds4"):
    assert need in ids, need
kinds={}
for m in d["data"]:
    kinds[m.get("kind","?")]=kinds.get(m.get("kind","?"),0)+1
assert kinds.get("lane",0)>=4
assert kinds.get("model",0)>=2
print("OK", kinds, "total", len(d["data"]))
PY

echo "== /v1/lanes populated =="
curl -fsS "$BASE/v1/lanes" -H "$AUTH" > "$TMP/lanes.json"
python3 - "$TMP/lanes.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
for k,v in d["lanes"].items():
    assert v["card_count"]>=2, k
    assert v["ready_count"]>=1, k
    print(f"  {k}: {v['ready_count']}/{v['card_count']} ready")
print("OK")
PY

echo "== model=lanes chat =="
curl -fsS "$BASE/v1/chat/completions" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"model":"lanes","messages":[{"role":"user","content":"show"}]}' > "$TMP/lanes-chat.json"
python3 -c "import json; t=json.load(open('$TMP/lanes-chat.json'))['choices'][0]['message']['content']; assert 'lane/smart' in t; print('OK', len(t), 'chars')"

echo "== independent no-key returns 400 =="
code=$(curl -s -o "$TMP/nokey.json" -w '%{http_code}' "$BASE/v1/chat/completions" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"model":"or/qwen3-coder","messages":[{"role":"user","content":"x"}]}')
test "$code" = "400"
python3 -c "import json; d=json.load(open('$TMP/nokey.json')); assert d['detail']['error']=='model_not_ready'; print('OK')"

echo
echo "VERIFY_LIVE PASSED"
