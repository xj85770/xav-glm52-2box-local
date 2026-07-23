#!/usr/bin/env bash
# serve.sh — foreground llama-server entrypoint (launched in a tmux session by launch.sh).
# Ceiling defaults live in cluster.env (KV_TYPE=f16, N_EXPERT_USED=5). Override at runtime:
#   CTX=8192 ./launch.sh
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"

# KV cache type (f16 default; q8_0 selectable).
KV_FLAGS=()
[ "${KV_TYPE:-f16}" = "q8_0" ] && KV_FLAGS=(-ctk q8_0 -ctv q8_0)

# Optional LExI-style global active-expert override (GGUF metadata override; zero model-code change).
# The key is "<arch>.expert_used_count"; set ARCH in cluster.env if your model's arch differs.
# NOTE: on some llama.cpp builds only certain values are stable over RPC (see docs/FINDINGS.md).
EXPERT_FLAGS=()
if [ -n "${N_EXPERT_USED:-}" ]; then
  EXPERT_FLAGS=(--override-kv "${ARCH:-glm-dsa}.expert_used_count=int:${N_EXPERT_USED}")
fi

exec "$LLAMA_BIN/llama-server" -m "$MODEL" --rpc "${NODE1_IP}:${RPC_PORT}" --device RPC0,MTL0 \
  -ngl 999 --no-mmap -fa on -c "${CTX:-16384}" --parallel 1 -b 256 -ub 256 \
  ${KV_FLAGS[@]+"${KV_FLAGS[@]}"} ${EXPERT_FLAGS[@]+"${EXPERT_FLAGS[@]}"} \
  --alias model --reasoning off \
  --host 127.0.0.1 --port "$SERVE_PORT" --jinja
