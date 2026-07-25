from __future__ import annotations

from rolodex_lib.lane_index import build_lane_rolodex, render_lanes_markdown, resolve_model_target
from rolodex_lib.lanes import LANE_NAMES


def test_every_lane_has_full_rolodex_from_catalog(local_only_env):
    index = build_lane_rolodex(environ=local_only_env)
    for lane in LANE_NAMES:
        assert lane in index["lanes"]
        cards = index["lanes"][lane]["cards"]
        assert len(cards) >= 2, lane
        # local fallbacks always ready
        assert index["lanes"][lane]["ready_count"] >= 1
        assert any(c["id"].startswith("local/") and c["ready"] for c in cards)


def test_lane_rolodex_includes_unkeyed_cards(local_only_env):
    index = build_lane_rolodex(environ=local_only_env)
    smart = index["lanes"]["lane/smart"]
    assert smart["card_count"] > smart["ready_count"]
    assert any(not c["ready"] for c in smart["cards"])
    assert "or/llama-3.3-70b" in smart["missing_key_ids"] or any(
        c["id"].startswith("or/") for c in smart["cards"]
    )


def test_resolve_model_target():
    assert resolve_model_target("lanes") == "lanes"
    assert resolve_model_target("smart") == "lane/smart"
    assert resolve_model_target("or/qwen3-coder") == "or/qwen3-coder"


def test_render_includes_individual_ids(local_only_env):
    text = render_lanes_markdown(build_lane_rolodex(environ=local_only_env))
    assert "lane/fast" in text
    assert "local/ds4" in text
