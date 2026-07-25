from __future__ import annotations

import pytest

from rolodex_lib.lanes import LANE_ALIASES, LANE_NAMES, resolve_lane
from rolodex_lib.runtime import build_runtime_config


def test_resolve_lane_aliases():
    assert resolve_lane("smart") == "lane/smart"
    assert resolve_lane("lane/code") == "lane/code"
    assert resolve_lane("lane-fast") == "lane/fast"
    with pytest.raises(KeyError):
        resolve_lane("turbo-ultra")


def test_describe_lanes_counts(local_only_env):
    cfg = build_runtime_config(environ=local_only_env)
    counts = {n: 0 for n in LANE_NAMES}
    for e in cfg["model_list"]:
        if e["model_name"] in counts:
            counts[e["model_name"]] += 1
    assert counts["lane/local"] >= 1
    # local fallbacks keep every lane non-empty
    assert counts["lane/fast"] >= 1
    assert counts["lane/smart"] >= 1
    assert counts["lane/code"] >= 1


def test_all_aliases_map_to_known_lanes():
    for alias, target in LANE_ALIASES.items():
        assert target in LANE_NAMES
        assert resolve_lane(alias) == target
