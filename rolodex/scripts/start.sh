#!/usr/bin/env bash
# start.sh — LiteLLM upstream (:4001) + rolodex gateway (:4000)
# Gateway exposes every individual model API id AND every lane.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PATH="${HOME}/.local/bin:${PATH}"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

: "${ROLODEX_PORT:=4000}"
: "${ROLODEX_UPSTREAM_PORT:=4001}"
: "${ROLODEX_MASTER_KEY:=sk-rolodex}"
: "${LOCAL_DS4_BASE:=http://127.0.0.1:8000/v1}"
: "${LOCAL_LLAMA_BASE:=http://127.0.0.1:8080/v1}"
: "${LOCAL_API_KEY:=local}"
: "${LOCAL_MODEL_ID:=glm-5.2}"
export ROLODEX_UPSTREAM="http://127.0.0.1:${ROLODEX_UPSTREAM_PORT}"
export ROLODEX_MASTER_KEY ROLODEX_PORT

python3 "$ROOT/scripts/build_runtime.py"
python3 "$ROOT/scripts/inventory.py" --write >/dev/null

if ! command -v litellm >/dev/null 2>&1; then
  echo "litellm not found on PATH. Install with:"
  echo "  python3 -m pip install -r $ROOT/requirements.txt"
  exit 1
fi

cleanup() {
  if [[ -n "${LITELLM_PID:-}" ]] && kill -0 "$LITELLM_PID" 2>/dev/null; then
    kill "$LITELLM_PID" 2>/dev/null || true
    wait "$LITELLM_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starting LiteLLM upstream on :${ROLODEX_UPSTREAM_PORT} ..."
litellm --config "$ROOT/config.runtime.yaml" --port "$ROLODEX_UPSTREAM_PORT" --host 127.0.0.1 &
LITELLM_PID=$!

# Wait for upstream health
for _ in $(seq 1 50); do
  if curl -fsS "http://127.0.0.1:${ROLODEX_UPSTREAM_PORT}/health" >/dev/null 2>&1 \
     || curl -fsS "http://127.0.0.1:${ROLODEX_UPSTREAM_PORT}/v1/models" \
          -H "Authorization: Bearer ${ROLODEX_MASTER_KEY}" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

echo "Rolodex gateway on http://127.0.0.1:${ROLODEX_PORT}/v1"
echo "Auth: Authorization: Bearer ${ROLODEX_MASTER_KEY}"
echo
echo "List everything:   GET /v1/models     (lanes + every individual model API)"
echo "Lane rolodexes:    GET /v1/lanes      or  model=lanes"
echo "Run a lane:        model=lane/smart   (failover across ready cards)"
echo "Run one model:     model=or/qwen3-coder | groq/llama-3.3-70b | local/ds4"
echo

exec python3 -m uvicorn rolodex_lib.gateway:create_app --factory \
  --host 127.0.0.1 --port "$ROLODEX_PORT"
