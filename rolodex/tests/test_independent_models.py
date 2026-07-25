from __future__ import annotations

from rolodex_lib.runtime import build_runtime_config, summarize_runtime


def test_ready_models_registered_independently_and_in_lanes(local_only_env):
    env = dict(local_only_env)
    env["GROQ_API_KEY"] = "gq"
    env["OPENROUTER_API_KEY"] = "or"
    cfg = build_runtime_config(environ=env)
    summary = summarize_runtime(cfg)

    # Independent API ids
    assert "groq/llama-3.3-70b" in summary["direct_models"]
    assert "or/qwen3-coder" in summary["direct_models"]
    assert "local/ds4" in summary["direct_models"]

    # Same cards also mounted on lanes
    assert "groq/llama-3.3-70b" in summary["lanes"]["lane/fast"]
    assert "or/qwen3-coder" in summary["lanes"]["lane/code"]

    # Independent entry has independent=True in model_info
    indep = next(e for e in cfg["model_list"] if e["model_name"] == "groq/llama-3.3-70b")
    assert indep["model_info"]["independent"] is True
    lane_entry = next(
        e
        for e in cfg["model_list"]
        if e["model_name"] == "lane/fast" and e["model_info"]["id"] == "groq/llama-3.3-70b"
    )
    assert lane_entry["model_info"]["independent"] is False


def test_all_four_lanes_always_present_with_local_fallback(local_only_env):
    cfg = build_runtime_config(environ=local_only_env)
    summary = summarize_runtime(cfg)
    for lane in ("lane/local", "lane/fast", "lane/smart", "lane/code"):
        assert lane in summary["lanes"], lane
        assert any(x.startswith("local/") for x in summary["lanes"][lane])


def test_litellm_model_info_tier_is_free_or_paid_or_omitted(local_only_env):
    """LiteLLM ModelInfo.tier only accepts free|paid — local/trial must not leak raw."""
    env = dict(local_only_env)
    env["HYPERBOLIC_API_KEY"] = "hy"
    env["GROQ_API_KEY"] = "gq"
    cfg = build_runtime_config(environ=env)
    for entry in cfg["model_list"]:
        info = entry["model_info"]
        assert "rolodex_tier" in info
        if "tier" in info:
            assert info["tier"] in ("free", "paid"), info
        if info["rolodex_tier"] == "local":
            assert "tier" not in info
        if info["rolodex_tier"] == "trial":
            assert info.get("tier") == "paid"
