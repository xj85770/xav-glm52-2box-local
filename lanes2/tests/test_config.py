from __future__ import annotations

from pathlib import Path

import yaml

from lanes2_lib.lanes import LANE_NAMES
from lanes2_lib.runtime import build_runtime_config, summarize_runtime, write_runtime_config


def test_local_only_runtime(local_only_env):
    cfg = build_runtime_config(environ=local_only_env)
    summary = summarize_runtime(cfg)
    # All four lanes present (local fallbacks on every lane)
    for lane in LANE_NAMES:
        assert lane in summary["lanes"], lane
        assert any(mid.startswith("local/") for mid in summary["lanes"][lane])
    # Direct/independent model ids also present
    assert "local/ds4" in summary["direct_models"]
    assert "local/llama" in summary["direct_models"]


def test_full_keys_enable_major_lanes(local_only_env):
    env = dict(local_only_env)
    env.update(
        {
            "OPENROUTER_API_KEY": "or",
            "GROQ_API_KEY": "gq",
            "CEREBRAS_API_KEY": "cb",
            "GEMINI_API_KEY": "gm",
            "MISTRAL_API_KEY": "ms",
            "COHERE_API_KEY": "co",
            "HF_TOKEN": "hf",
            "GITHUB_TOKEN": "gh",
            "CLOUDFLARE_API_TOKEN": "cf",
            "CLOUDFLARE_ACCOUNT_ID": "acct",
            "NVIDIA_API_KEY": "nv",
            "FIREWORKS_API_KEY": "fw",
            "HYPERBOLIC_API_KEY": "hy",
            "SAMBANOVA_API_KEY": "sn",
            "SCALEWAY_API_KEY": "sc",
            "DASHSCOPE_API_KEY": "ds",
        }
    )
    cfg = build_runtime_config(environ=env)
    summary = summarize_runtime(cfg)
    for lane in LANE_NAMES:
        assert lane in summary["lanes"], lane
    assert summary["total_cards"] >= 40
    assert "or/llama-3.3-70b" in summary["direct_models"]
    assert "groq/llama-3.3-70b" in summary["direct_models"]


def test_lane_allowlist(local_only_env):
    env = dict(local_only_env)
    env["LANES2_LANES"] = "local,code"
    env["GROQ_API_KEY"] = "gq"
    cfg = build_runtime_config(environ=env)
    summary = summarize_runtime(cfg)
    assert set(summary["lanes"]) == {"lane/local", "lane/code"}


def test_tier_filter_skips_trial(local_only_env):
    env = dict(local_only_env)
    env["LANES2_TIERS"] = "local,free"
    env["HYPERBOLIC_API_KEY"] = "hy"
    env["GROQ_API_KEY"] = "gq"
    cfg = build_runtime_config(environ=env)
    summary = summarize_runtime(cfg)
    assert "hyp/llama-3.3-70b" not in summary["direct_models"]
    assert "groq/llama-3.3-70b" in summary["direct_models"]


def test_write_runtime_roundtrip(tmp_path, local_only_env):
    out = tmp_path / "config.runtime.yaml"
    write_runtime_config(out, environ=local_only_env)
    loaded = yaml.safe_load(out.read_text())
    assert loaded["model_list"]
    assert any(e["model_name"] == "lane/local" for e in loaded["model_list"])


def test_catalog_file_exists():
    assert (Path(__file__).resolve().parents[1] / "catalog.yaml").is_file()


def test_model_info_carries_context_limits(local_only_env):
    env = dict(local_only_env)
    env["GROQ_API_KEY"] = "gq"
    cfg = build_runtime_config(environ=env)
    groq = next(e for e in cfg["model_list"] if e["model_name"] == "groq/llama-3.3-70b")
    info = groq["model_info"]
    assert info["context"] >= 1000
    assert info["tps_typical"] > 0
    assert info["rpd"] == 1000
