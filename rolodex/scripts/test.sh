#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="${HOME}/.local/bin:${PATH}"
cd "$ROOT"
python3 -m pip install -q -r "$ROOT/requirements.txt"
python3 "$ROOT/scripts/build_runtime.py"
python3 -m pytest "$ROOT/tests"
echo "ALL ROLODEX TESTS PASSED"
