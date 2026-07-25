from __future__ import annotations

from rolodex_lib.catalog import model_by_id
from rolodex_lib.runtime import model_available, summarize_runtime, build_runtime_config


def test_model_available_requires_cloud_key():
    m = model_by_id("groq/llama-3.3-70b")
    assert model_available(m, environ={}) is False
    assert model_available(m, environ={"GROQ_API_KEY": "x"}) is True


def test_local_always_available():
    m = model_by_id("local/ds4")
    assert model_available(m, environ={}) is True


def test_cloudflare_needs_account_and_token():
    m = model_by_id("cf/glm-5.2")
    assert model_available(m, environ={"CLOUDFLARE_API_TOKEN": "t"}) is False
    assert model_available(
        m, environ={"CLOUDFLARE_API_TOKEN": "t", "CLOUDFLARE_ACCOUNT_ID": "a"}
    ) is True


def test_summarize_runtime(local_only_env):
    cfg = build_runtime_config(environ=local_only_env)
    summary = summarize_runtime(cfg)
    assert summary["total_cards"] >= 2
    assert "lane/local" in summary["lanes"]
