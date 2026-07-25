#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="${HOME}/.local/bin:${PATH}"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT"
python3 -m pip install -q -r "$ROOT/requirements.txt"
python3 "$ROOT/scripts/build_runtime.py"
# Guard: LiteLLM rejects model_info.tier outside free|paid
python3 - <<'PY'
import yaml
cfg=yaml.safe_load(open("config.runtime.yaml"))
for e in cfg["model_list"]:
    t=e.get("model_info",{}).get("tier")
    assert t in (None, "free", "paid")
    assert "rolodex_tier" in e["model_info"]
print("runtime model_info tiers OK")
PY
python3 -m pytest "$ROOT/tests"
echo "ALL ROLODEX TESTS PASSED"
