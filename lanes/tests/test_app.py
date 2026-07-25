from __future__ import annotations

import json

import httpx
import pytest
from fastapi.testclient import TestClient

import app as lanes_app


class FakeResp:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text or json.dumps(payload or {})

    def json(self):
        return self._payload


@pytest.fixture
def client(monkeypatch):
    async def fake_lanes2(method, path, **kwargs):
        if path == "/health":
            return FakeResp(200, {"status": "ok", "service": "lanes2-gateway"})
        if path == "/v1/models":
            return FakeResp(
                200,
                {
                    "object": "list",
                    "data": [
                        {"id": "lanes", "kind": "lane-index"},
                        {"id": "lane/smart", "kind": "lane", "ready": True, "ready_count": 2, "card_count": 10},
                        {
                            "id": "local/ds4",
                            "kind": "model",
                            "ready": True,
                            "context": 131072,
                            "tps_typical": 3,
                        },
                        {
                            "id": "or/qwen3-coder",
                            "kind": "model",
                            "ready": False,
                            "requires_env": "OPENROUTER_API_KEY",
                        },
                    ],
                },
            )
        if path == "/v1/lanes":
            return FakeResp(
                200,
                {
                    "lanes": {
                        "lane/smart": {"ready_count": 2, "card_count": 10, "cards": []},
                        "lane/fast": {"ready_count": 1, "card_count": 8, "cards": []},
                        "lane/code": {"ready_count": 1, "card_count": 6, "cards": []},
                        "lane/local": {"ready_count": 2, "card_count": 3, "cards": []},
                    }
                },
            )
        if path == "/v1/chat/completions":
            body = kwargs.get("json") or {}
            return FakeResp(
                200,
                {
                    "id": "chatcmpl-test",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": f"echo:{body.get('messages', [{}])[-1].get('content')}",
                            }
                        }
                    ],
                },
            )
        return FakeResp(404, text="missing")

    monkeypatch.setattr(lanes_app, "SESSIONS", {})
    c = TestClient(lanes_app.create_app())

    # Patch the bound method used inside routes by replacing helper on module via app dependency:
    # easiest: monkeypatch httpx at call sites through replacing create_app's closure — instead
    # patch at module by wrapping create_app routes using TestClient + monkeypatching
    # the async helper after import by replacing app.dependency — we'll patch httpx.AsyncClient.
    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def request(self, method, url, headers=None, **kwargs):
            path = url.replace(lanes_app.LANES2_BASE, "")
            return await fake_lanes2(method, path, **kwargs)

        async def stream(self, method, url, headers=None, json=None):
            raise RuntimeError("stream not used in non-stream tests")

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    return c


def test_health_and_models(client):
    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["service"] == "lanes-dashboard"
    assert h.json()["lanes2_health"]["ok"] is True

    m = client.get("/api/models")
    assert m.status_code == 200
    ids = {x["id"] for x in m.json()["data"]}
    assert "lane/smart" in ids
    assert "local/ds4" in ids


def test_chat_non_stream_wires_to_lanes2(client):
    r = client.post(
        "/api/chat",
        json={"model": "lane/smart", "content": "hello agent", "stream": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["message"]["content"] == "echo:hello agent"
    assert body["session_id"]
    sid = body["session_id"]
    s = client.get(f"/api/sessions/{sid}")
    assert len(s.json()["messages"]) == 2


def test_index_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "lanes" in r.text.lower()
