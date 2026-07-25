#!/usr/bin/env python3
"""lanes — local agent dashboard chat, fully wired to lanes2 backend."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

LANES2_BASE = os.environ.get("LANES2_BASE", "http://127.0.0.1:4000").rstrip("/")
LANES2_KEY = os.environ.get("LANES2_MASTER_KEY", "sk-lanes2")
LANES_PORT = int(os.environ.get("LANES_PORT", "3000"))
DEFAULT_MODEL = os.environ.get("LANES_DEFAULT_MODEL", "lane/smart")

# In-memory sessions for the local dashboard
SESSIONS: dict[str, dict[str, Any]] = {}


def create_app() -> FastAPI:
    app = FastAPI(title="lanes", version="1.0.0")
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

    def _headers() -> dict[str, str]:
        return {
            "Authorization": f"Bearer {LANES2_KEY}",
            "Content-Type": "application/json",
        }

    async def _lanes2(method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{LANES2_BASE}{path}"
        timeout = httpx.Timeout(600.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.request(method, url, headers=_headers(), **kwargs)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/health")
    async def health() -> dict[str, Any]:
        backend = {"ok": False, "detail": None}
        try:
            r = await _lanes2("GET", "/health")
            backend = {"ok": r.status_code == 200, "detail": r.json() if r.status_code == 200 else r.text}
        except Exception as exc:  # noqa: BLE001
            backend = {"ok": False, "detail": str(exc)}
        return {
            "status": "ok" if backend["ok"] else "degraded",
            "service": "lanes-dashboard",
            "lanes2": LANES2_BASE,
            "lanes2_health": backend,
            "default_model": DEFAULT_MODEL,
        }

    @app.get("/api/models")
    async def api_models() -> JSONResponse:
        """Proxy lanes2 model list — lanes + every individual API id."""
        try:
            r = await _lanes2("GET", "/v1/models")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"lanes2 unreachable: {exc}") from exc
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return JSONResponse(r.json())

    @app.get("/api/lanes")
    async def api_lanes() -> JSONResponse:
        try:
            r = await _lanes2("GET", "/v1/lanes")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"lanes2 unreachable: {exc}") from exc
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return JSONResponse(r.json())

    @app.get("/api/sessions")
    def list_sessions() -> dict[str, Any]:
        out = []
        for sid, sess in SESSIONS.items():
            out.append(
                {
                    "id": sid,
                    "title": sess.get("title") or "chat",
                    "model": sess.get("model"),
                    "messages": len(sess.get("messages") or []),
                    "updated_at": sess.get("updated_at"),
                }
            )
        out.sort(key=lambda x: x.get("updated_at") or 0, reverse=True)
        return {"sessions": out}

    @app.post("/api/sessions")
    async def create_session(request: Request) -> dict[str, Any]:
        body = await request.json()
        model = str(body.get("model") or DEFAULT_MODEL)
        sid = uuid.uuid4().hex[:12]
        SESSIONS[sid] = {
            "id": sid,
            "title": body.get("title") or "New chat",
            "model": model,
            "messages": [],
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        return SESSIONS[sid]

    @app.get("/api/sessions/{sid}")
    def get_session(sid: str) -> dict[str, Any]:
        if sid not in SESSIONS:
            raise HTTPException(status_code=404, detail="session not found")
        return SESSIONS[sid]

    @app.delete("/api/sessions/{sid}")
    def delete_session(sid: str) -> dict[str, str]:
        SESSIONS.pop(sid, None)
        return {"status": "deleted"}

    @app.post("/api/chat")
    async def chat(request: Request):
        """Agent chat → lanes2 /v1/chat/completions (supports stream)."""
        body = await request.json()
        sid = str(body.get("session_id") or "")
        model = str(body.get("model") or DEFAULT_MODEL)
        content = str(body.get("content") or "").strip()
        stream = bool(body.get("stream", True))

        if not content:
            raise HTTPException(status_code=400, detail="empty content")

        if not sid or sid not in SESSIONS:
            sid = uuid.uuid4().hex[:12]
            SESSIONS[sid] = {
                "id": sid,
                "title": content[:48],
                "model": model,
                "messages": [],
                "created_at": time.time(),
                "updated_at": time.time(),
            }

        sess = SESSIONS[sid]
        sess["model"] = model
        if sess.get("title") in (None, "", "New chat"):
            sess["title"] = content[:48]
        sess["messages"].append({"role": "user", "content": content})
        sess["updated_at"] = time.time()

        payload = {
            "model": model,
            "messages": sess["messages"],
            "stream": stream,
            "temperature": body.get("temperature", 0.4),
            "max_tokens": body.get("max_tokens", 2048),
        }

        if not stream:
            try:
                r = await _lanes2("POST", "/v1/chat/completions", json=payload)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=502, detail=f"lanes2 unreachable: {exc}") from exc
            if r.status_code >= 400:
                raise HTTPException(status_code=r.status_code, detail=r.text)
            data = r.json()
            reply = data["choices"][0]["message"]["content"]
            sess["messages"].append({"role": "assistant", "content": reply})
            sess["updated_at"] = time.time()
            return {"session_id": sid, "model": model, "message": {"role": "assistant", "content": reply}, "raw": data}

        async def gen():
            yield f"data: {json.dumps({'type': 'session', 'session_id': sid, 'model': model})}\n\n"
            parts: list[str] = []
            try:
                timeout = httpx.Timeout(600.0, connect=5.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream(
                        "POST",
                        f"{LANES2_BASE}/v1/chat/completions",
                        headers=_headers(),
                        json=payload,
                    ) as resp:
                        if resp.status_code >= 400:
                            err = (await resp.aread()).decode("utf-8", errors="replace")
                            yield f"data: {json.dumps({'type': 'error', 'error': err})}\n\n"
                            return
                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            if line.startswith("data: "):
                                chunk = line[6:].strip()
                                if chunk == "[DONE]":
                                    break
                                try:
                                    obj = json.loads(chunk)
                                except json.JSONDecodeError:
                                    continue
                                delta = (
                                    ((obj.get("choices") or [{}])[0].get("delta") or {}).get("content")
                                    or ((obj.get("choices") or [{}])[0].get("message") or {}).get("content")
                                )
                                if delta:
                                    parts.append(delta)
                                    yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"
                                # Non-stream fallback shape from lanes meta model
                                if not delta and obj.get("choices"):
                                    msg = (obj["choices"][0].get("message") or {}).get("content")
                                    if msg:
                                        parts.append(msg)
                                        yield f"data: {json.dumps({'type': 'token', 'content': msg})}\n\n"
            except Exception as exc:  # noqa: BLE001
                yield f"data: {json.dumps({'type': 'error', 'error': str(exc)})}\n\n"
                return

            full = "".join(parts)
            if full:
                sess["messages"].append({"role": "assistant", "content": full})
                sess["updated_at"] = time.time()
            yield f"data: {json.dumps({'type': 'done', 'session_id': sid})}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    return app


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app:create_app",
        factory=True,
        host="127.0.0.1",
        port=LANES_PORT,
        reload=False,
        app_dir=str(ROOT),
    )


if __name__ == "__main__":
    main()
