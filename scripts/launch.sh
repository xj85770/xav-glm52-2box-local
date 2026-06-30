#!/usr/bin/env bash
# launch.sh — bring up a 2-node llama.cpp RPC decode for a large MoE GGUF, the hardened way.
#   NODE0 (here) = coordinator (owns weights, runs llama-server).
#   NODE1        = worker (rpc-server over the fast link, Metal-pinned).
#
# Why all the gates: a ~100GB+ Metal load onto a busy/just-booted worker, or onto a worker
# still holding the previous load's residency, reliably crashes the RPC path and can wedge the
# node. Each gate below is there because skipping it caused a real crash. Run ON NODE0.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
RUNDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_LOG="$RUNDIR/server.log"
SERVER_ENTRY="$RUNDIR/serve.sh"
TMUX_SESSION="${TMUX_SESSION:-moe2box}"

# ---- 0. Sanity --------------------------------------------------------------
say "NODE0 host: $(hostname 2>/dev/null || echo unknown)"
for t in tmux python3 curl ssh; do
  command -v "$t" >/dev/null || die "missing required tool: $t"
done
[ -f "$MODEL" ] || die "Model not found at \$MODEL ($MODEL)."
[ -x "$LLAMA_BIN/llama-server" ] || die "llama-server not executable at \$LLAMA_BIN ($LLAMA_BIN)."

# ---- 1. GATE A: fast link reachable ----------------------------------------
say "GATE A: confirming NODE1 fast link $NODE1_IP ..."
link_up || die "NODE1 $NODE1_IP not reachable. Bring the fast link up (see LINK_PIN_CMD in cluster.env). Nothing started."
say "GATE A passed."

# ---- 2. GATE B: SSH-exec reachable -----------------------------------------
say "GATE B: confirming SSH-exec to $NODE1_SSH ..."
QM_MEM="$($SSH 'sysctl -n hw.memsize' 2>/dev/null || true)"
[ -n "${QM_MEM:-}" ] || die "SSH-exec to NODE1 failed (ping worked, sshd did not). Nothing started."
say "GATE B passed (NODE1 hw.memsize=$QM_MEM)."
$SSH "test -x $RPC_BIN_REMOTE" || die "rpc-server not executable on NODE1 at $RPC_BIN_REMOTE. Build/copy the SAME patched build first."

# ---- 3. GATE C: NODE1 settled ----------------------------------------------
if [ "${SKIP_SETTLE_GATE:-0}" != "1" ]; then
  say "GATE C: waiting for NODE1 1-min loadavg < ${SETTLE_LOAD:-2.5} ..."
  settled=""
  for i in $(seq 1 40); do
    la="$($SSH "sysctl -n vm.loadavg 2>/dev/null | awk '{print \$2}'" 2>/dev/null || echo 99)"
    if awk "BEGIN{exit !(${la:-99} < ${SETTLE_LOAD:-2.5})}"; then say "GATE C passed (loadavg $la)."; settled=1; break; fi
    say "  NODE1 loadavg $la — waiting 15s ..."; sleep 15
  done
  [ -n "$settled" ] || die "GATE C: NODE1 never settled. Let it quiet down or SKIP_SETTLE_GATE=1."
fi

# ---- 4. start Metal-pinned worker ------------------------------------------
start_worker(){
  $SSH "pkill -x rpc-server 2>/dev/null; sleep 1; \
        nohup $RPC_BIN_REMOTE -H 0.0.0.0 -p $RPC_PORT -d MTL0 >/tmp/moe2box-rpc.log 2>&1 & \
        sleep 2; pgrep -x rpc-server >/dev/null && echo WORKER_UP || echo WORKER_FAIL"
}
say "Starting NODE1 rpc-server (-d MTL0) ..."
start_worker | tee /tmp/moe2box-worker.txt
grep -q WORKER_UP /tmp/moe2box-worker.txt || die "NODE1 rpc-server failed to start (see NODE1:/tmp/moe2box-rpc.log)."

cleanup_worker(){ say "Tearing down NODE1 worker ..."; $SSH "pkill -INT -x rpc-server; sleep 2; pkill -KILL -x rpc-server 2>/dev/null; true" || true; }

# ---- 5. SMOKE: tiny model over RPC (optional) ------------------------------
if [ -f "${SMOKE_1B:-/nonexistent}" ]; then
  say "SMOKE: 1B over RPC (force onto RPC0) ..."
  S="$("$LLAMA_BIN/llama-completion" -m "$SMOKE_1B" --rpc "${NODE1_IP}:${RPC_PORT}" --device RPC0 -ngl 99 \
        --temp 0 -p 'The capital of France is' -n 8 -no-cnv 2>/dev/null || true)"
  printf '%s' "$S" | grep -qi paris && say "SMOKE passed." || { cleanup_worker; die "SMOKE failed: 1B over RPC did not say Paris. Link/worker broken."; }
fi

# ---- 6. restart worker (reclaim any smoke residency before the big load) ----
say "Restarting NODE1 worker clean before serve ..."
$SSH "pkill -INT -x rpc-server; sleep 2; pkill -KILL -x rpc-server 2>/dev/null; sleep 1; \
      nohup $RPC_BIN_REMOTE -H 0.0.0.0 -p $RPC_PORT -d MTL0 >/tmp/moe2box-rpc.log 2>&1 & \
      sleep 3; pgrep -x rpc-server >/dev/null && echo OK || echo FAIL" | grep -q OK \
  || die "NODE1 worker failed to restart clean before serve."

# ---- 7. GATE D: NODE1 has headroom for the serve load ----------------------
if [ "${SKIP_MEM_GATE:-0}" != "1" ]; then
  say "GATE D: confirming NODE1 free RAM >= ${MIN_FREE_GB:-90} GiB ..."
  FREE="$(node1_free_gb)"; say "GATE D: NODE1 ~${FREE} GiB free."
  awk "BEGIN{exit !(${FREE:-0} >= ${MIN_FREE_GB:-90})}" \
    || { cleanup_worker; die "GATE D: NODE1 only ~${FREE} GiB free (< ${MIN_FREE_GB:-90}); restart did not reclaim residency. Worker torn down."; }
  say "GATE D passed."
fi

# ---- 8. serve --------------------------------------------------------------
say "Launching llama-server on 127.0.0.1:${SERVE_PORT} (log: $SERVER_LOG) ..."
pkill -f 'llama-server' 2>/dev/null || true; sleep 1
tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true
: > "$SERVER_LOG"
export KV_TYPE CTX N_EXPERT_USED ARCH SETTLE_LOAD MIN_FREE_GB RPC_PORT SERVE_PORT NODE1_IP
tmux new-session -d -s "$TMUX_SESSION" "$SERVER_ENTRY >>'$SERVER_LOG' 2>&1"
say "Waiting for /health (cold load can take 1-3 min) ..."
for i in $(seq 1 120); do
  if curl -s "http://127.0.0.1:${SERVE_PORT}/health" 2>/dev/null | grep -qi '"ok"'; then
    say "Server healthy on :${SERVE_PORT}. Run ./verify.sh to measure decode t/s + cold-check output."
    exit 0
  fi
  tmux has-session -t "$TMUX_SESSION" 2>/dev/null || { echo "--- server.log tail ---"; tail -30 "$SERVER_LOG"; cleanup_worker; die "llama-server died during startup (see $SERVER_LOG). Worker torn down."; }
  sleep 2
done
echo "--- server.log tail ---"; tail -30 "$SERVER_LOG"; cleanup_worker
die "Server never reported healthy. Worker torn down (no half-loaded residency left on NODE1)."
