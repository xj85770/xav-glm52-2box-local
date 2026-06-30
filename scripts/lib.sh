#!/usr/bin/env bash
# lib.sh — shared helpers. Sourced by launch.sh / serve.sh / verify.sh.
# Loads cluster.env from the same directory and exposes SSH + logging helpers.
set -uo pipefail

_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -f "$_DIR/cluster.env" ]; then
  echo "FATAL: $_DIR/cluster.env not found. Copy cluster.env.example -> cluster.env and fill it in." >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$_DIR/cluster.env"

SSH="ssh -o BatchMode=yes -o ConnectTimeout=8 -o IdentitiesOnly=yes -i $SSH_KEY $NODE1_SSH"

ts(){ date '+%Y-%m-%d %H:%M:%S'; }
say(){ printf '[%s] %s\n' "$(ts)" "$*"; }
die(){ printf '[%s] ABORT: %s\n' "$(ts)" "$*" >&2; exit 1; }

# Re-assert the worker's fast-link IP if a pin command is configured, then confirm reachability.
link_up(){
  [ -n "${LINK_PIN_CMD:-}" ] && eval "$LINK_PIN_CMD" >/dev/null 2>&1
  local w; for w in 1 2 3; do
    ping -c1 -t2 "$NODE1_IP" >/dev/null 2>&1 && return 0
    sleep 4
  done
  ping -c2 -t2 "$NODE1_IP" >/dev/null 2>&1
}

# NODE1 available RAM in GiB (free + inactive + speculative).
node1_free_gb(){
  $SSH 'vm_stat | awk "/Pages free/{f=\$3}/Pages inactive/{ia=\$3}/Pages speculative/{sp=\$3} END{gsub(/\./,\"\",f);gsub(/\./,\"\",ia);gsub(/\./,\"\",sp); print int((f+ia+sp)*16384/1073741824)}"' 2>/dev/null || echo 0
}
