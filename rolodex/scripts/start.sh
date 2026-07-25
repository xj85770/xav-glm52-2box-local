#!/usr/bin/env bash
# start.sh — build runtime config and launch the LiteLLM rolodex proxy.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PATH="${HOME}/.local/bin:${PATH}"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

: "${ROLODEX_PORT:=4000}"
: "${ROLODEX_MASTER_KEY:=sk-rolodex}"
: "${LOCAL_DS4_BASE:=http://127.0.0.1:8000/v1}"
: "${LOCAL_LLAMA_BASE:=http://127.0.0.1:8080/v1}"
: "${LOCAL_API_KEY:=local}"
: "${LOCAL_MODEL_ID:=glm-5.2}"

python3 "$ROOT/scripts/build_runtime.py"
python3 "$ROOT/scripts/inventory.py" --write >/dev/null

if ! command -v litellm >/dev/null 2>&1; then
  echo "litellm not found on PATH. Install with:"
  echo "  python3 -m pip install -r $ROOT/requirements.txt"
  exit 1
fi

echo "Rolodex listening on http://127.0.0.1:${ROLODEX_PORT}/v1"
echo "Auth: Authorization: Bearer ${ROLODEX_MASTER_KEY}"
echo "Lanes: lane/local | lane/fast | lane/smart | lane/code"
echo "Or swap by exact id from: $ROOT/state/AGENT_CONTEXT.md"
echo "Refresh inventory anytime: ./scripts/inventory.py"
exec litellm --config "$ROOT/config.runtime.yaml" --port "$ROLODEX_PORT" --host 127.0.0.1
