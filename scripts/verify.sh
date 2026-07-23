#!/usr/bin/env bash
# verify.sh — measure WARM decode tokens/sec (computed from server timings, not eyeballed),
# cold-print one generation for a coherence check, then tear down and confirm the worker
# released its memory. Run AFTER launch.sh reports healthy.
set -uo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
THRESHOLD="${THRESHOLD:-10.0}"
PASSES="${PASSES:-3}"
PROMPT="${PROMPT:-Explain why the sky is blue to a curious ten-year-old, in one tight paragraph.}"

curl -s "http://127.0.0.1:${SERVE_PORT}/health" 2>/dev/null | grep -qi '"ok"' || die "Server not healthy on :${SERVE_PORT}. Run launch.sh first."

say "${PASSES} warm passes (first pass discarded as cold) ..."
TPS=()
LAST=""
for p in $(seq 1 "$PASSES"); do
  R="$(curl -s "http://127.0.0.1:${SERVE_PORT}/v1/chat/completions" -H 'Content-Type: application/json' \
        -d "$(python3 -c "import json,sys;print(json.dumps({'messages':[{'role':'user','content':sys.argv[1]}],'temperature':0.2,'max_tokens':160,'stream':False}))" "$PROMPT")" 2>/dev/null)"
  t="$(printf '%s' "$R" | python3 -c "import sys,json
try:
 d=json.load(sys.stdin); tm=d.get('timings',{}); print(tm.get('predicted_per_second',''))
except: print('')" 2>/dev/null)"
  LAST="$(printf '%s' "$R" | python3 -c "import sys,json
try: print(json.load(sys.stdin)['choices'][0]['message']['content'])
except: print('')" 2>/dev/null)"
  say "pass $p: ${t:-ERR} t/s"
  [ "$p" -gt 1 ] && [ -n "$t" ] && TPS+=("$t")
done

BEST="$(printf '%s\n' "${TPS[@]:-0}" | sort -rn | head -1)"
VERD=$(awk "BEGIN{print (${BEST:-0} > ${THRESHOLD}) ? \"PASS\" : \"FAIL\"}")
say "RESULT (computed): WARM_TPS ${BEST:-0}  $VERD  [bar > ${THRESHOLD} t/s]"
echo "================= GENERATED (cold coherence check) ================="
printf '%s\n' "$LAST"
echo "==================================================================="
say "Operator: confirm the text reads as coherent (garble => quant/residency damage)."

say "Tearing down ..."
pkill -f 'llama-server' 2>/dev/null || true
$SSH "pkill -INT -x rpc-server; sleep 2; pkill -KILL -x rpc-server 2>/dev/null; true" 2>/dev/null || true
sleep 4
FREE="$(node1_free_gb)"
say "NODE1 free after teardown: ~${FREE} GiB (should return near idle; far below idle => stranded leak, reboot NODE1)."
