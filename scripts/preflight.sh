#!/usr/bin/env bash
# preflight.sh — sanity checks before a ceiling launch. Run on NODE0.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"

say "PREFLIGHT: model file ..."
[ -f "$MODEL" ] || die "Model not found: $MODEL"
MODEL_GB="$(du -g "$MODEL" 2>/dev/null | awk '{print $1}' || echo 0)"
say "  MODEL=$MODEL (~${MODEL_GB} GiB on disk — must be readable from NODE0 internal storage, not streamed from external NVMe during serve)"

say "PREFLIGHT: llama-server binary ..."
[ -x "$LLAMA_BIN/llama-server" ] || die "llama-server missing at $LLAMA_BIN"

say "PREFLIGHT: NODE1 SSH ..."
QM_MEM="$($SSH 'sysctl -n hw.memsize' 2>/dev/null || true)"
[ -n "${QM_MEM:-}" ] || die "SSH to NODE1 failed"
say "  NODE1 hw.memsize=$QM_MEM"

say "PREFLIGHT: NODE1 rpc-server ..."
$SSH "test -x $RPC_BIN_REMOTE" || die "rpc-server not executable on NODE1 at $RPC_BIN_REMOTE (build/copy identical patched binaries)"

say "PREFLIGHT: fast link (primary + optional backup) ..."
ACTIVE="$(select_fast_link)" || die "No fast link reachable. Check NODE1_IP / NODE1_IP_BACKUP and Thunderbolt bridges."
export NODE1_IP="$ACTIVE"
say "  Active RPC link: $NODE1_IP"

say "PREFLIGHT: NODE1 free RAM ..."
FREE="$(node1_free_gb)"
say "  NODE1 ~${FREE} GiB free (need >= ${MIN_FREE_GB:-90} GiB before heavy load; reboot NODE1 if low)"
awk "BEGIN{exit !(${FREE:-0} >= ${MIN_FREE_GB:-90})}" \
  || say "  WARN: NODE1 below ${MIN_FREE_GB:-90} GiB — launch may fail GATE D; consider rebooting NODE1."

say "PREFLIGHT: smoke model (optional) ..."
if [ -f "${SMOKE_1B:-/nonexistent}" ]; then
  say "  SMOKE_1B present at $SMOKE_1B"
else
  say "  SMOKE_1B not set — RPC link smoke will be skipped at launch"
fi

say "PREFLIGHT OK — ready for ceiling launch."
