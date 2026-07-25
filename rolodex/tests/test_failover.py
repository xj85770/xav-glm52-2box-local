from __future__ import annotations

import os

import pytest

from rolodex_lib.mock_upstream import MockUpstream


@pytest.fixture
def ordered_mocks():
    primary = MockUpstream("primary").start()
    secondary = MockUpstream("secondary").start()
    try:
        yield primary, secondary
    finally:
        primary.stop()
        secondary.stop()


def _router_for(primary: MockUpstream, secondary: MockUpstream):
    from litellm import Router

    model_list = [
        {
            "model_name": "lane/fast",
            "litellm_params": {
                "model": "openai/mock-primary",
                "api_base": primary.base_url,
                "api_key": "test",
                "order": 1,
            },
        },
        {
            "model_name": "lane/fast",
            "litellm_params": {
                "model": "openai/mock-secondary",
                "api_base": secondary.base_url,
                "api_key": "test",
                "order": 2,
            },
        },
    ]
    return Router(
        model_list=model_list,
        num_retries=2,
        timeout=10,
        set_verbose=False,
        allowed_fails=1,
        cooldown_time=1,
    )


def test_mock_upstream_basic(ordered_mocks):
    import httpx

    primary, _ = ordered_mocks
    r = httpx.post(
        f"{primary.base_url}/chat/completions",
        json={"model": "x", "messages": [{"role": "user", "content": "hi"}]},
        timeout=5,
    )
    assert r.status_code == 200
    assert r.json()["choices"][0]["message"]["content"] == "ok-from-primary"


def test_router_uses_primary_when_healthy(ordered_mocks):
    primary, secondary = ordered_mocks
    router = _router_for(primary, secondary)
    resp = router.completion(
        model="lane/fast",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=16,
    )
    text = resp.choices[0].message.content
    assert "primary" in text
    assert len(primary.state.calls) == 1
    assert len(secondary.state.calls) == 0


def test_router_failsover_to_secondary_on_429(ordered_mocks):
    primary, secondary = ordered_mocks
    primary.state.fail_times = 3
    router = _router_for(primary, secondary)
    resp = router.completion(
        model="lane/fast",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=16,
    )
    text = resp.choices[0].message.content
    assert "secondary" in text
    assert len(secondary.state.calls) >= 1


def test_router_failsover_when_primary_down(ordered_mocks):
    primary, secondary = ordered_mocks
    primary.state.healthy = False
    router = _router_for(primary, secondary)
    resp = router.completion(
        model="lane/fast",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=16,
    )
    assert "secondary" in resp.choices[0].message.content


def test_cross_lane_fallback_chain(ordered_mocks):
    """Simulate smart → local style fallback across model groups."""
    from litellm import Router

    primary, secondary = ordered_mocks
    router = Router(
        model_list=[
            {
                "model_name": "lane/smart",
                "litellm_params": {
                    "model": "openai/smart",
                    "api_base": primary.base_url,
                    "api_key": "test",
                },
            },
            {
                "model_name": "lane/local",
                "litellm_params": {
                    "model": "openai/local",
                    "api_base": secondary.base_url,
                    "api_key": "test",
                },
            },
        ],
        fallbacks=[{"lane/smart": ["lane/local"]}],
        num_retries=1,
        timeout=10,
        set_verbose=False,
        allowed_fails=1,
        cooldown_time=1,
    )
    primary.state.healthy = False
    resp = router.completion(
        model="lane/smart",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=16,
    )
    assert "secondary" in resp.choices[0].message.content


def test_runtime_cards_are_litellm_router_compatible(local_only_env, ordered_mocks):
    """Build runtime lane/local pointing at mocks and complete successfully."""
    from litellm import Router

    from rolodex_lib.runtime import build_runtime_config

    primary, secondary = ordered_mocks
    env = dict(local_only_env)
    env["LOCAL_DS4_BASE"] = primary.base_url
    env["LOCAL_LLAMA_BASE"] = secondary.base_url
    cfg = build_runtime_config(environ=env)
    local_cards = [e for e in cfg["model_list"] if e["model_name"] == "lane/local"]
    assert len(local_cards) >= 2

    # LiteLLM reads os.environ for os.environ/… refs — materialize for router test
    model_list = []
    for entry in local_cards:
        params = dict(entry["litellm_params"])
        # resolve os.environ refs manually for Router unit usage
        for k, v in list(params.items()):
            if isinstance(v, str) and v.startswith("os.environ/"):
                key = v.split("/", 1)[1]
                params[k] = env.get(key) or os.environ.get(key)
        # api_base already rewritten? build_runtime keeps os.environ refs
        if params.get("api_base", "").startswith("os.environ/"):
            key = params["api_base"].split("/", 1)[1]
            params["api_base"] = env[key]
        if params.get("api_key", "").startswith("os.environ/"):
            key = params["api_key"].split("/", 1)[1]
            params["api_key"] = env[key]
        model_list.append({"model_name": "lane/local", "litellm_params": params})

    primary.state.fail_times = 2
    router = Router(
        model_list=model_list,
        num_retries=2,
        timeout=10,
        set_verbose=False,
        allowed_fails=1,
        cooldown_time=1,
    )
    resp = router.completion(
        model="lane/local",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=16,
    )
    assert "secondary" in resp.choices[0].message.content
