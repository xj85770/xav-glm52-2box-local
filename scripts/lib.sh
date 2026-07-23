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

# Ping an IP with short retries.
_ping_ip(){
  local ip="$1" w
  for w in 1 2 3; do
    ping -c1 -t2 "$ip" >/dev/null 2>&1 && return 0
    sleep 2
  done
  ping -c2 -t2 "$ip" >/dev/null 2>&1
}

# Optional per-link pin commands (dual TB5: primary cable + backup cable).
_pin_link(){
  local which="$1"
  local cmd=""
  case "$which" in
    primary)   cmd="${LINK_PIN_CMD:-}" ;;
    backup)    cmd="${LINK_PIN_CMD_BACKUP:-}" ;;
  esac
  [ -n "$cmd" ] && eval "$cmd" >/dev/null 2>&1
}

# Pick the best reachable fast-link IP. Primary first, then backup. Echoes the winner.
select_fast_link(){
  local ip label
  for entry in "primary:${NODE1_IP}" "backup:${NODE1_IP_BACKUP:-}"; do
    label="${entry%%:*}"
    ip="${entry#*:}"
    [ -z "$ip" ] && continue
    _pin_link "$label"
    if _ping_ip "$ip"; then
      [ "$label" = "backup" ] && say "WARN: primary link down — using backup $ip"
      printf '%s' "$ip"
      return 0
    fi
  done
  return 1
}

# Re-assert link IPs if configured, select active fast link, confirm reachability.
link_up(){
  local active
  active="$(select_fast_link)" || return 1
  NODE1_IP="$active"
  export NODE1_IP
  return 0
}

# NODE1 available RAM in GiB (free + inactive + speculative).
node1_free_gb(){
  $SSH 'vm_stat | awk "/Pages free/{f=\$3}/Pages inactive/{ia=\$3}/Pages speculative/{sp=\$3} END{gsub(/\./,\"\",f);gsub(/\./,\"\",ia);gsub(/\./,\"\",sp); print int((f+ia+sp)*16384/1073741824)}"' 2>/dev/null || echo 0
}
