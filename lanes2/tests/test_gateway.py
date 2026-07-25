from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(local_only_env, monkeypatch):
    for k, v in local_only_env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("LANES2_MASTER_KEY", "sk-test")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    from lanes2_lib.gateway import create_app

    return TestClient(create_app())


def test_v1_models_lists_lanes_and_individual_apis(client):
    r = client.get("/v1/models", headers={"Authorization": "Bearer sk-test"})
    assert r.status_code == 200
    data = r.json()["data"]
    ids = {m["id"] for m in data}
    assert "lanes" in ids
    assert "lane/local" in ids
    assert "lane/fast" in ids
    assert "lane/smart" in ids
    assert "lane/code" in ids
    # individual APIs
    assert "local/ds4" in ids
    assert "groq/llama-3.3-70b" in ids
    assert "or/qwen3-coder" in ids
    kinds = {m["id"]: m.get("kind") for m in data}
    assert kinds["lane/smart"] == "lane"
    assert kinds["local/ds4"] == "model"
    groq = next(m for m in data if m["id"] == "groq/llama-3.3-70b")
    assert groq["ready"] is True
    orphan = next(m for m in data if m["id"] == "or/qwen3-coder")
    assert orphan["ready"] is False
    assert "code" in orphan["lanes"]


def test_v1_lanes_populated(client):
    r = client.get("/v1/lanes", headers={"Authorization": "Bearer sk-test"})
    assert r.status_code == 200
    body = r.json()
    assert body["lanes"]["lane/code"]["card_count"] >= 5
    assert "groq/llama-3.3-70b" in body["lanes"]["lane/fast"]["ready_ids"]


def test_chat_model_lanes_returns_rolodex(client):
    r = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer sk-test"},
        json={"model": "lanes", "messages": [{"role": "user", "content": "show"}]},
    )
    assert r.status_code == 200
    text = r.json()["choices"][0]["message"]["content"]
    assert "lane/smart" in text
    assert "local/ds4" in text


def test_independent_model_without_key_errors(client):
    r = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer sk-test"},
        json={
            "model": "or/qwen3-coder",
            "messages": [{"role": "user", "content": "hi"}],
        },
    )
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["error"] == "model_not_ready"
    assert "OPENROUTER" in detail["requires_env"]
