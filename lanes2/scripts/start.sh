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

# Defaults — must be exported so LiteLLM child resolves os.environ/* refs.
export LANES2_PORT="${LANES2_PORT:-4000}"
export LANES2_UPSTREAM_PORT="${LANES2_UPSTREAM_PORT:-4001}"
export LANES2_MASTER_KEY="${LANES2_MASTER_KEY:-sk-lanes2}"
export LANES2_UPSTREAM="http://127.0.0.1:${LANES2_UPSTREAM_PORT}"
export LOCAL_DS4_BASE="${LOCAL_DS4_BASE:-http://127.0.0.1:8000/v1}"
export LOCAL_LLAMA_BASE="${LOCAL_LLAMA_BASE:-http://127.0.0.1:8080/v1}"
export LOCAL_API_KEY="${LOCAL_API_KEY:-local}"
export LOCAL_MODEL_ID="${LOCAL_MODEL_ID:-glm-5.2}"

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

echo "Starting LiteLLM upstream on :${LANES2_UPSTREAM_PORT} ..."
litellm --config "$ROOT/config.runtime.yaml" --port "$LANES2_UPSTREAM_PORT" --host 127.0.0.1 &
LITELLM_PID=$!

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${LANES2_UPSTREAM_PORT}/v1/models" \
        -H "Authorization: Bearer ${LANES2_MASTER_KEY}" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$LITELLM_PID" 2>/dev/null; then
    echo "LiteLLM exited early. Last log lines:"
    wait "$LITELLM_PID" || true
    exit 1
  fi
  sleep 0.25
done

if ! curl -fsS "http://127.0.0.1:${LANES2_UPSTREAM_PORT}/v1/models" \
      -H "Authorization: Bearer ${LANES2_MASTER_KEY}" >/dev/null 2>&1; then
  echo "LiteLLM did not become ready on :${LANES2_UPSTREAM_PORT}"
  exit 1
fi

echo "lanes2 gateway on http://127.0.0.1:${LANES2_PORT}/v1"
echo "Auth: Authorization: Bearer ${LANES2_MASTER_KEY}"
echo
echo "List everything:   GET /v1/models     (lanes + every individual model API)"
echo "Lane rolodexes:    GET /v1/lanes      or  model=lanes"
echo "Run a lane:        model=lane/smart   (failover across ready cards)"
echo "Run one model:     model=or/qwen3-coder | groq/llama-3.3-70b | local/ds4"
echo

exec python3 -m uvicorn lanes2_lib.gateway:create_app --factory \
  --host 127.0.0.1 --port "$LANES2_PORT"
