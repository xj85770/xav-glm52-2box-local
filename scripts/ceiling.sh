#!/usr/bin/env bash
# ceiling.sh — one-shot path to documented ~18.5 tok/s decode on 2× M5 Max.
# Runs preflight, launches with ceiling defaults, then extended warm verify.
#
# Usage (on NODE0, after cluster.env is filled in):
#   scripts/ceiling.sh
#
# Override any tunable via env, e.g.:
#   CTX=8192 scripts/ceiling.sh
set -euo pipefail
RUNDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Documented ceiling defaults (see docs/FINDINGS.md).
export KV_TYPE="${KV_TYPE:-f16}"
export N_EXPERT_USED="${N_EXPERT_USED:-5}"
export CTX="${CTX:-16384}"
export THRESHOLD="${THRESHOLD:-17.0}"
export PASSES="${PASSES:-5}"

say(){ printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

say "=== CEILING RUN ==="
say "Config: KV_TYPE=$KV_TYPE N_EXPERT_USED=$N_EXPERT_USED CTX=$CTX THRESHOLD=$THRESHOLD PASSES=$PASSES"

"$RUNDIR/preflight.sh"

say "Launching 2-box serve ..."
"$RUNDIR/launch.sh"

say "Measuring warm decode (ceiling bar: >${THRESHOLD} tok/s) ..."
"$RUNDIR/verify.sh"
