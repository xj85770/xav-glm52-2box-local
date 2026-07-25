"""Tiny OpenAI-compatible mock upstream for failover tests."""

from __future__ import annotations

import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn


@dataclass
class MockState:
    name: str
    fail_times: int = 0
    calls: list[dict[str, Any]] = field(default_factory=list)
    healthy: bool = True


def _free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def make_app(state: MockState) -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, str]:
        if not state.healthy:
            raise HTTPException(status_code=503, detail="down")
        return {"status": "ok", "name": state.name}

    @app.get("/v1/models")
    def models() -> dict[str, Any]:
        return {
            "object": "list",
            "data": [{"id": state.name, "object": "model", "owned_by": "mock"}],
        }

    @app.post("/v1/chat/completions")
    async def chat(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        body = await request.json()
        state.calls.append({"authorization": authorization, "body": body})
        if state.fail_times > 0:
            state.fail_times -= 1
            raise HTTPException(status_code=429, detail=f"{state.name} rate limited")
        if not state.healthy:
            raise HTTPException(status_code=503, detail=f"{state.name} down")

        content = f"ok-from-{state.name}"
        return JSONResponse(
            {
                "id": f"chatcmpl-{state.name}",
                "object": "chat.completion",
                "model": body.get("model", state.name),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 8,
                    "completion_tokens": 4,
                    "total_tokens": 12,
                },
            }
        )

    return app


class MockUpstream:
    def __init__(self, name: str, host: str = "127.0.0.1", port: int | None = None):
        self.state = MockState(name=name)
        self.host = host
        self.port = port or _free_port(host)
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}/v1"

    def start(self) -> "MockUpstream":
        app = make_app(self.state)
        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="warning",
            lifespan="off",
        )
        server = uvicorn.Server(config)
        # Prevent uvicorn from installing its own signal handlers in a thread.
        server.install_signal_handlers = lambda: None  # type: ignore[method-assign]
        self._server = server

        thread = threading.Thread(target=server.run, name=f"mock-{self.state.name}", daemon=True)
        self._thread = thread
        thread.start()

        deadline = time.time() + 5.0
        while time.time() < deadline:
            if server.started:
                break
            time.sleep(0.02)
        else:
            raise RuntimeError(f"mock upstream {self.state.name} failed to start on {self.port}")

        # readiness probe
        import httpx

        for _ in range(50):
            try:
                r = httpx.get(f"http://{self.host}:{self.port}/health", timeout=0.2)
                if r.status_code in (200, 503):
                    return self
            except Exception:
                time.sleep(0.05)
        raise RuntimeError(f"mock upstream {self.state.name} not reachable on {self.port}")

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=3)
