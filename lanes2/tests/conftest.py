from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def local_only_env():
    return {
        "LOCAL_DS4_BASE": "http://127.0.0.1:8000/v1",
        "LOCAL_LLAMA_BASE": "http://127.0.0.1:8080/v1",
        "LOCAL_API_KEY": "local",
        "LOCAL_MODEL_ID": "glm-5.2",
        "LANES2_MASTER_KEY": "sk-test",
    }


@pytest.fixture
def base_config(local_only_env):
    """Runtime config with local cards only (compat name for failover tests)."""
    from lanes2_lib.runtime import build_runtime_config

    return build_runtime_config(environ=local_only_env)
