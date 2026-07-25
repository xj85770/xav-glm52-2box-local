"""Build LiteLLM runtime config from catalog.yaml + available env keys."""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml

from .catalog import iter_models, load_catalog
from .lanes import LANE_ALIASES, LANE_NAMES, resolve_lane

DEFAULTS = {
    "LOCAL_DS4_BASE": "http://127.0.0.1:8000/v1",
    "LOCAL_LLAMA_BASE": "http://127.0.0.1:8080/v1",
    "LOCAL_API_KEY": "local",
    "LOCAL_MODEL_ID": "glm-5.2",
    "ROLODEX_MASTER_KEY": "sk-rolodex",
    "ROLODEX_PORT": "4000",
    "VERCEL_AI_GATEWAY_BASE": "https://ai-gateway.vercel.sh/v1",
    "OPENCODE_ZEN_BASE": "https://opencode.ai/zen/v1",
    "SCALEWAY_API_BASE": "https://api.scaleway.ai/v1",
}


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def raw_env(name: str, environ: dict[str, str] | None = None) -> str | None:
    env = environ if environ is not None else os.environ
    raw = env.get(name)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def env_value(name: str, environ: dict[str, str] | None = None) -> str | None:
    got = raw_env(name, environ)
    if got is not None:
        return got
    return DEFAULTS.get(name)


def model_available(model: dict[str, Any], environ: dict[str, str] | None = None) -> bool:
    if model.get("tier") == "local":
        return True
    req = model.get("provider_requires_env") or model.get("api_key_env")
    if req and not raw_env(str(req), environ):
        return False
    for extra in model.get("provider_requires_env_extra") or []:
        # MODAL_TOKEN_SECRET etc. — require if listed
        if not raw_env(str(extra), environ) and str(extra) not in DEFAULTS:
            # allow api_base defaults
            if str(extra).endswith("_BASE") and env_value(str(extra), environ):
                continue
            if not raw_env(str(extra), environ):
                return False
    key_env = model.get("api_key_env")
    if key_env and key_env != "LOCAL_API_KEY" and not raw_env(str(key_env), environ):
        return False
    base_env = model.get("api_base_env")
    if base_env and base_env not in DEFAULTS and not raw_env(str(base_env), environ):
        # local bases have defaults; custom bases must be set
        if not str(base_env).startswith("LOCAL_"):
            return False
    return True


def _resolve_litellm_model(model: dict[str, Any], environ: dict[str, str] | None) -> str:
    lit = str(model["litellm_model"])
    local_id = env_value("LOCAL_MODEL_ID", environ) or "glm-5.2"
    return lit.replace("LOCAL_MODEL_ID", local_id)


def _card_entry(model: dict[str, Any], *, lane: str | None, environ: dict[str, str] | None) -> dict[str, Any]:
    """Build one LiteLLM model_list entry. lane=None → direct model id card."""
    short_lane = lane.split("/", 1)[1] if lane and lane.startswith("lane/") else lane
    params: dict[str, Any] = {
        "model": _resolve_litellm_model(model, environ),
    }
    key_env = model.get("api_key_env") or model.get("provider_requires_env")
    if key_env:
        params["api_key"] = f"os.environ/{key_env}"
    elif model.get("tier") == "local":
        params["api_key"] = "os.environ/LOCAL_API_KEY"

    if model.get("api_base"):
        params["api_base"] = model["api_base"]
    elif model.get("api_base_env"):
        params["api_base"] = f"os.environ/{model['api_base_env']}"

    if model.get("rpm") is not None:
        params["rpm"] = int(model["rpm"])
    if model.get("tpm") is not None:
        params["tpm"] = int(model["tpm"])

    order = 50
    if lane and short_lane:
        order = int((model.get("order_in_lane") or {}).get(short_lane, 50))
    params["order"] = order

    if model.get("tier") == "local":
        params["timeout"] = 600

    model_name = lane if lane else model["id"]
    model_info = {
        "id": model["id"],
        "display": model.get("display"),
        "provider": model.get("provider_id"),
        "tier": model.get("tier"),
        "lane": short_lane,
        "context": model.get("context"),
        "tps_typical": model.get("tps_typical"),
        "rpm": model.get("rpm"),
        "rpd": model.get("rpd"),
        "tpm": model.get("tpm"),
        "tpd": model.get("tpd"),
        "mode": "chat",
    }
    if model.get("provider_requires_env"):
        model_info["requires_env"] = model.get("provider_requires_env")
    return {
        "model_name": model_name,
        "litellm_params": params,
        "model_info": model_info,
    }


def _allowed_lanes(environ: dict[str, str] | None) -> set[str] | None:
    env = environ if environ is not None else os.environ
    raw = str(env.get("ROLODEX_LANES", "")).strip()
    if not raw:
        return None
    return {resolve_lane(part.strip()) for part in raw.split(",") if part.strip()}


def _allowed_tiers(environ: dict[str, str] | None) -> set[str] | None:
    env = environ if environ is not None else os.environ
    raw = str(env.get("ROLODEX_TIERS", "")).strip()
    if not raw:
        return {"local", "free", "trial"}
    return {p.strip() for p in raw.split(",") if p.strip()}


def build_runtime_config(
    catalog: dict[str, Any] | None = None,
    environ: dict[str, str] | None = None,
    *,
    include_direct_models: bool = True,
) -> dict[str, Any]:
    cat = catalog if catalog is not None else load_catalog()
    allowed_lanes = _allowed_lanes(environ)
    allowed_tiers = _allowed_tiers(environ) or {"local", "free", "trial"}

    model_list: list[dict[str, Any]] = []
    present_lanes: set[str] = set()
    present_models: set[str] = set()

    for model in iter_models(cat):
        if model.get("tier") not in allowed_tiers:
            continue
        if not model_available(model, environ):
            continue

        # Direct callable model id (for explicit swap)
        if include_direct_models:
            model_list.append(_card_entry(model, lane=None, environ=environ))
            present_models.add(model["id"])

        for short in model.get("lanes") or []:
            lane = f"lane/{short}"
            if lane not in LANE_NAMES:
                continue
            if allowed_lanes is not None and lane not in allowed_lanes:
                continue
            model_list.append(_card_entry(model, lane=lane, environ=environ))
            present_lanes.add(lane)

    aliases = {a: t for a, t in LANE_ALIASES.items() if t in present_lanes}
    # Also alias bare model ids already present — no-op
    for mid in present_models:
        aliases[mid] = mid

    cfg: dict[str, Any] = {
        "model_list": model_list,
        "litellm_settings": {
            "drop_params": True,
            "num_retries": 2,
            "request_timeout": 120,
            "allowed_fails": 2,
            "cooldown_time": 60,
            "callbacks": ["rolodex_lib.callbacks.proxy_handler_instance"],
        },
        "router_settings": {
            "routing_strategy": "simple-shuffle",
            "num_retries": 1,
            "timeout": 120,
            "enable_pre_call_checks": True,
            "model_group_alias": aliases,
        },
        "general_settings": {
            "master_key": (
                f"os.environ/ROLODEX_MASTER_KEY"
                if raw_env("ROLODEX_MASTER_KEY", environ)
                else DEFAULTS["ROLODEX_MASTER_KEY"]
            ),
        },
    }
    return cfg


def write_runtime_config(
    out_path: Path | None = None,
    *,
    catalog_path: Path | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    out = out_path or (_root() / "config.runtime.yaml")
    cat = load_catalog(catalog_path)
    cfg = build_runtime_config(cat, environ=environ)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(cfg, fh, sort_keys=False)
    return out


def summarize_runtime(cfg: dict[str, Any]) -> dict[str, Any]:
    lanes: dict[str, list[str]] = {n: [] for n in LANE_NAMES}
    directs: list[str] = []
    for entry in cfg.get("model_list", []):
        name = entry.get("model_name")
        info = entry.get("model_info") or {}
        mid = str(info.get("id") or entry.get("litellm_params", {}).get("model"))
        if name in lanes:
            if mid not in lanes[name]:
                lanes[name].append(mid)
        else:
            directs.append(str(name))
    return {
        "lanes": {k: v for k, v in lanes.items() if v},
        "direct_models": sorted(set(directs)),
        "total_cards": len(cfg.get("model_list", [])),
        "aliases": (cfg.get("router_settings") or {}).get("model_group_alias") or {},
    }


# Back-compat for older tests
def load_base_config(path: Path | None = None) -> dict[str, Any]:
    """Deprecated: returns a runtime-shaped config from catalog (all cards, no env filter)."""
    # Preserve enough for tests that still import this — prefer catalog.
    return build_runtime_config(environ={k: v for k, v in DEFAULTS.items()}, include_direct_models=True)


def card_available(entry: dict[str, Any], environ: dict[str, str] | None = None) -> bool:
    """Back-compat helper used by older tests."""
    info = entry.get("model_info") or {}
    # Reconstruct minimal model dict
    req = info.get("requires_env")
    fake = {
        "tier": info.get("tier") or ("local" if (info.get("lane") == "local") else "free"),
        "provider_requires_env": req,
        "api_key_env": req,
        "provider_requires_env_extra": [],
    }
    if fake["tier"] == "local" or (info.get("id") or "").startswith("local/"):
        fake["tier"] = "local"
    return model_available(fake, environ)
