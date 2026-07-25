#!/usr/bin/env bash
# start-stack.sh — fully wired: lanes2 (API rolodex) + lanes (agent dashboard chat)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="${HOME}/.local/bin:${PATH}"

export LANES2_PORT="${LANES2_PORT:-4000}"
export LANES2_UPSTREAM_PORT="${LANES2_UPSTREAM_PORT:-4001}"
export LANES2_MASTER_KEY="${LANES2_MASTER_KEY:-sk-lanes2}"
export LANES2_UPSTREAM="http://127.0.0.1:${LANES2_UPSTREAM_PORT}"
export LANES2_BASE="http://127.0.0.1:${LANES2_PORT}"
export LANES_PORT="${LANES_PORT:-3000}"
export LANES_DEFAULT_MODEL="${LANES_DEFAULT_MODEL:-lane/smart}"
export LOCAL_DS4_BASE="${LOCAL_DS4_BASE:-http://127.0.0.1:8000/v1}"
export LOCAL_LLAMA_BASE="${LOCAL_LLAMA_BASE:-http://127.0.0.1:8080/v1}"
export LOCAL_API_KEY="${LOCAL_API_KEY:-local}"
export LOCAL_MODEL_ID="${LOCAL_MODEL_ID:-glm-5.2}"
export PYTHONPATH="${REPO}/lanes2${PYTHONPATH:+:$PYTHONPATH}"

if [[ -f "$REPO/lanes2/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO/lanes2/.env"
  set +a
  export LANES2_BASE="http://127.0.0.1:${LANES2_PORT:-4000}"
  export LANES2_UPSTREAM="http://127.0.0.1:${LANES2_UPSTREAM_PORT:-4001}"
fi

cleanup() {
  [[ -n "${LITELLM_PID:-}" ]] && kill "$LITELLM_PID" 2>/dev/null || true
  [[ -n "${GATEWAY_PID:-}" ]] && kill "$GATEWAY_PID" 2>/dev/null || true
  [[ -n "${LANES_PID:-}" ]] && kill "$LANES_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "== building lanes2 runtime =="
python3 "$REPO/lanes2/scripts/build_runtime.py"

if ! command -v litellm >/dev/null 2>&1; then
  echo "Install deps: python3 -m pip install -r $REPO/lanes2/requirements.txt"
  exit 1
fi

echo "== LiteLLM :${LANES2_UPSTREAM_PORT} =="
litellm --config "$REPO/lanes2/config.runtime.yaml" --port "$LANES2_UPSTREAM_PORT" --host 127.0.0.1 &
LITELLM_PID=$!

for _ in $(seq 1 60); do
  curl -fsS "http://127.0.0.1:${LANES2_UPSTREAM_PORT}/v1/models" \
    -H "Authorization: Bearer ${LANES2_MASTER_KEY}" >/dev/null 2>&1 && break
  sleep 0.25
done

echo "== lanes2 gateway :${LANES2_PORT} =="
python3 -m uvicorn lanes2_lib.gateway:create_app --factory \
  --host 127.0.0.1 --port "$LANES2_PORT" --app-dir "$REPO/lanes2" &
GATEWAY_PID=$!

for _ in $(seq 1 40); do
  curl -fsS "http://127.0.0.1:${LANES2_PORT}/health" >/dev/null 2>&1 && break
  sleep 0.2
done

echo "== lanes dashboard :${LANES_PORT} =="
python3 -m uvicorn app:create_app --factory \
  --host 127.0.0.1 --port "$LANES_PORT" --app-dir "$REPO/lanes" &
LANES_PID=$!

for _ in $(seq 1 40); do
  curl -fsS "http://127.0.0.1:${LANES_PORT}/health" >/dev/null 2>&1 && break
  sleep 0.2
done

echo
echo "Ready."
echo "  lanes chat UI : http://127.0.0.1:${LANES_PORT}"
echo "  lanes2 API    : http://127.0.0.1:${LANES2_PORT}/v1"
echo "  default model : ${LANES_DEFAULT_MODEL}"
echo
echo "Open the UI and chat. Lane pills + model dropdown are populated from lanes2."
wait
