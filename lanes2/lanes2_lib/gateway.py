"""lanes2 gateway — lists every individual model API + lanes; proxies chat to LiteLLM."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .inventory import build_inventory
from .lane_index import build_lane_rolodex, render_lanes_markdown, resolve_model_target
from .lanes import LANE_NAMES
from .catalog import iter_models, load_catalog
from .runtime import DEFAULTS, env_value, model_available


def create_app() -> FastAPI:
    app = FastAPI(title="lanes2", version="1.0.0")
    upstream = os.environ.get("LANES2_UPSTREAM", "http://127.0.0.1:4001").rstrip("/")
    master = env_value("LANES2_MASTER_KEY") or DEFAULTS["LANES2_MASTER_KEY"]

    def _auth(authorization: str | None) -> None:
        if not authorization:
            raise HTTPException(status_code=401, detail="missing Authorization bearer")
        token = authorization.removeprefix("Bearer ").strip()
        if token != master:
            raise HTTPException(status_code=401, detail="invalid API key")

    def _environ() -> dict[str, str]:
        return {k: v for k, v in os.environ.items() if isinstance(v, str)}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "lanes2-gateway"}

    @app.get("/v1/lanes")
    def list_lanes(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        _auth(authorization)
        return build_lane_rolodex(environ=_environ())

    @app.get("/v1/lanes/{lane_id:path}")
    def get_lane(lane_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        _auth(authorization)
        target = resolve_model_target(lane_id)
        if target == "lanes":
            return build_lane_rolodex(environ=_environ())
        if not target.startswith("lane/"):
            # allow /v1/lanes/smart
            try:
                from .lanes import resolve_lane

                target = resolve_lane(lane_id)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
        index = build_lane_rolodex(environ=_environ())
        lane = index["lanes"].get(target)
        if not lane:
            raise HTTPException(status_code=404, detail=f"unknown lane {lane_id}")
        return lane

    @app.get("/v1/models")
    def list_models(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        """OpenAI-style list: lanes first, then every individual model API id."""
        _auth(authorization)
        env = _environ()
        index = build_lane_rolodex(environ=env)
        data: list[dict[str, Any]] = []

        # Meta: type `lanes` to dump the rolodex
        data.append(
            {
                "id": "lanes",
                "object": "model",
                "owned_by": "lanes2",
                "kind": "lane-index",
                "description": "List all lanes with fully populated model rolodexes",
            }
        )

        for lane_name in LANE_NAMES:
            lane = index["lanes"][lane_name]
            data.append(
                {
                    "id": lane_name,
                    "object": "model",
                    "owned_by": "lanes2",
                    "kind": "lane",
                    "ready": lane["ready_count"] > 0,
                    "card_count": lane["card_count"],
                    "ready_count": lane["ready_count"],
                    "ready_ids": lane["ready_ids"],
                    "aliases": lane["aliases"],
                    "description": lane["description"],
                }
            )
            for alias in lane["aliases"]:
                data.append(
                    {
                        "id": alias,
                        "object": "model",
                        "owned_by": "lanes2",
                        "kind": "lane-alias",
                        "alias_of": lane_name,
                    }
                )

        # Every individual model API (independent of lanes)
        for row in build_inventory(environ=env, only_available=False):
            data.append(
                {
                    "id": row["id"],
                    "object": "model",
                    "owned_by": row.get("provider") or "lanes2",
                    "kind": "model",
                    "ready": row["available"],
                    "display": row.get("display"),
                    "provider": row.get("provider"),
                    "tier": row.get("tier"),
                    "lanes": row.get("lanes") or [],
                    "context": row.get("context"),
                    "tps_typical": row.get("tps_typical"),
                    "tps_observed": row.get("tps_observed"),
                    "limits": row.get("limits"),
                    "remaining": {
                        "requests_left_day": (row.get("remaining") or {}).get("requests_left_day"),
                        "tokens_left_day": (row.get("remaining") or {}).get("tokens_left_day"),
                        "tokens_left_total": (row.get("remaining") or {}).get("tokens_left_total"),
                    },
                    "requires_env": row.get("requires_env"),
                }
            )

        return {"object": "list", "data": data}

    @app.post("/v1/chat/completions")
    async def chat(
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        _auth(authorization)
        body = await request.json()
        model = str(body.get("model") or "")
        target = resolve_model_target(model)

        # model=lanes → return populated rolodex as the assistant message
        if target == "lanes":
            index = build_lane_rolodex(environ=_environ())
            text = render_lanes_markdown(index)
            return {
                "id": "chatcmpl-lanes",
                "object": "chat.completion",
                "model": "lanes",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }

        # Independent model id — must be ready (key present)
        if not target.startswith("lane/"):
            cat_models = {m["id"]: m for m in iter_models(load_catalog())}
            if target in cat_models:
                m = cat_models[target]
                if not model_available(m, _environ()):
                    key = m.get("provider_requires_env") or m.get("api_key_env") or "API_KEY"
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "model_not_ready",
                            "model": target,
                            "message": f"Set {key} in lanes2/.env to run this model independently.",
                            "lanes": m.get("lanes") or [],
                            "requires_env": key,
                        },
                    )
            body = dict(body)
            body["model"] = target
        else:
            body = dict(body)
            body["model"] = target

        # Proxy to LiteLLM upstream
        stream = bool(body.get("stream"))
        headers = {
            "Authorization": f"Bearer {master}",
            "Content-Type": "application/json",
        }
        url = f"{upstream}/v1/chat/completions"
        timeout = httpx.Timeout(600.0, connect=10.0)

        if stream:
            client = httpx.AsyncClient(timeout=timeout)

            async def gen():
                try:
                    async with client.stream("POST", url, json=body, headers=headers) as resp:
                        if resp.status_code >= 400:
                            err = await resp.aread()
                            yield err
                            return
                        async for chunk in resp.aiter_bytes():
                            yield chunk
                finally:
                    await client.aclose()

            return StreamingResponse(gen(), media_type="text/event-stream")

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=body, headers=headers)
            try:
                payload = resp.json()
            except Exception:
                raise HTTPException(status_code=resp.status_code, detail=resp.text) from None
            if resp.status_code >= 400:
                return JSONResponse(status_code=resp.status_code, content=payload)
            return JSONResponse(content=payload)

    return app


def main() -> None:
    import uvicorn

    port = int(env_value("LANES2_PORT") or "4000")
    uvicorn.run(
        "lanes2_lib.gateway:create_app",
        factory=True,
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
