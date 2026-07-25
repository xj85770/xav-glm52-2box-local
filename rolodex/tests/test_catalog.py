from __future__ import annotations

from rolodex_lib.catalog import iter_models, lane_members, load_catalog
from rolodex_lib.lanes import LANE_NAMES


def test_catalog_loads_and_has_many_models():
    cat = load_catalog()
    models = iter_models(cat)
    assert len(models) >= 60
    providers = {m["provider_id"] for m in models}
    for must in ("local", "openrouter", "google", "groq", "cerebras", "cloudflare", "hyperbolic", "scaleway"):
        assert must in providers


def test_every_model_has_context_and_tps():
    for m in iter_models():
        assert m.get("context"), m["id"]
        assert m.get("tps_typical") is not None, m["id"]
        assert m.get("display"), m["id"]
        assert m.get("litellm_model"), m["id"]


def test_lanes_have_members():
    for lane in LANE_NAMES:
        members = lane_members(lane)
        assert members, lane


def test_openrouter_free_models_present():
    ids = {m["id"] for m in iter_models()}
    assert "or/llama-3.3-70b" in ids
    assert "or/qwen3-coder" in ids
    assert "or/nemotron-3-super-120b" in ids
