from __future__ import annotations

from lanes2_lib.inventory import build_inventory, render_markdown, write_agent_context
from lanes2_lib.quota import QuotaStore, remaining_for_model
from lanes2_lib.catalog import model_by_id


def test_inventory_rows_include_limits_and_remaining(local_only_env, tmp_path):
    store = QuotaStore(tmp_path / "usage.json")
    store.record(model_id="groq/llama-3.3-70b", provider_id="groq", prompt_tokens=100, completion_tokens=50, tps=180.0)
    env = dict(local_only_env)
    env["GROQ_API_KEY"] = "gq"
    rows = build_inventory(environ=env, store=store)
    by_id = {r["id"]: r for r in rows}
    assert by_id["local/ds4"]["available"] is True
    assert by_id["groq/llama-3.3-70b"]["available"] is True
    assert by_id["or/llama-3.3-70b"]["available"] is False
    g = by_id["groq/llama-3.3-70b"]
    assert g["context"] == 131072
    assert g["tps_typical"] == 200
    assert g["tps_observed"] == 180.0
    assert g["remaining"]["requests_left_day"] == 1000 - 1
    assert "YES" in render_markdown(rows)


def test_remaining_shared_openrouter_quota(tmp_path):
    store = QuotaStore(tmp_path / "usage.json")
    store.record(model_id="or/llama-3.3-70b", provider_id="openrouter", prompt_tokens=10, completion_tokens=10)
    store.record(model_id="or/qwen3-coder", provider_id="openrouter", prompt_tokens=10, completion_tokens=10)
    m = model_by_id("or/llama-3.3-70b")
    rem = remaining_for_model(m, store.get_model(m["id"]), store.get_provider("openrouter"))
    # shared: 2 requests on provider day bucket
    assert rem["shared_quota"] is True
    assert rem["requests_left_day"] == 50 - 2


def test_write_agent_context(tmp_path, local_only_env):
    out = tmp_path / "AGENT_CONTEXT.md"
    path = write_agent_context(out, environ=local_only_env)
    text = path.read_text()
    assert "lane/local" in text or "local/ds4" in text
    assert "ctx" in text.lower() or "context" in text.lower() or "|" in text
    assert out.with_suffix(".json").is_file()
