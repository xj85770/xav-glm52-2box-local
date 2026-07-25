"""Local quota / usage tracker so inventory can show tokens & requests left."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _utc_hour() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")


def _utc_minute() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")


@dataclass
class UsageBucket:
    requests: int = 0
    tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    last_tps: float | None = None
    last_latency_ms: float | None = None
    last_used_at: float | None = None


class QuotaStore:
    """JSON-backed usage store keyed by model id and provider id."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"models": {}, "providers": {}}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"models": {}, "providers": {}}

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)

    def record(
        self,
        *,
        model_id: str,
        provider_id: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float | None = None,
        tps: float | None = None,
    ) -> None:
        total = int(prompt_tokens) + int(completion_tokens)
        day = _utc_day()
        hour = _utc_hour()
        minute = _utc_minute()
        now = time.time()
        with self._lock:
            for scope, key in (("models", model_id), ("providers", provider_id)):
                node = self._data.setdefault(scope, {}).setdefault(
                    key,
                    {
                        "day": day,
                        "hour": hour,
                        "minute": minute,
                        "day_requests": 0,
                        "day_tokens": 0,
                        "hour_requests": 0,
                        "hour_tokens": 0,
                        "minute_requests": 0,
                        "minute_tokens": 0,
                        "lifetime_requests": 0,
                        "lifetime_tokens": 0,
                        "last_tps": None,
                        "last_latency_ms": None,
                        "last_used_at": None,
                    },
                )
                if node.get("day") != day:
                    node["day"] = day
                    node["day_requests"] = 0
                    node["day_tokens"] = 0
                if node.get("hour") != hour:
                    node["hour"] = hour
                    node["hour_requests"] = 0
                    node["hour_tokens"] = 0
                if node.get("minute") != minute:
                    node["minute"] = minute
                    node["minute_requests"] = 0
                    node["minute_tokens"] = 0
                node["day_requests"] += 1
                node["day_tokens"] += total
                node["hour_requests"] += 1
                node["hour_tokens"] += total
                node["minute_requests"] += 1
                node["minute_tokens"] += total
                node["lifetime_requests"] += 1
                node["lifetime_tokens"] += total
                if tps is not None:
                    node["last_tps"] = float(tps)
                if latency_ms is not None:
                    node["last_latency_ms"] = float(latency_ms)
                node["last_used_at"] = now
            self._save()

    def get_model(self, model_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._data.get("models", {}).get(model_id) or {})

    def get_provider(self, provider_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._data.get("providers", {}).get(provider_id) or {})


def remaining_for_model(model: dict[str, Any], usage: dict[str, Any], provider_usage: dict[str, Any]) -> dict[str, Any]:
    """Compute remaining quota fields from catalog limits + local usage."""
    shared = bool(model.get("provider_shared_quota"))
    src = provider_usage if shared else usage

    def left(limit_key: str, used_key: str) -> int | None:
        limit = model.get(limit_key)
        if limit is None:
            # provider-level limits
            plim = model.get("provider_limits") or {}
            # map rpm_month etc.
            if limit_key == "rpd" and "rpm_month" in plim and model.get("rpd") is None:
                # approximate month→day for display only
                limit = max(1, int(plim["rpm_month"] // 30))
            else:
                limit = plim.get(
                    {
                        "rpm": "rpm",
                        "rpd": "rpd",
                        "tpm": "tpm",
                        "tpd": "tpd",
                        "rph": "rph",
                        "tph": "tph",
                    }.get(limit_key, limit_key)
                )
        if limit is None:
            return None
        used = int(src.get(used_key) or 0)
        return max(0, int(limit) - used)

    # minute ≈ rpm, hour ≈ rph/tph, day ≈ rpd/tpd
    out = {
        "requests_left_minute": left("rpm", "minute_requests"),
        "requests_left_hour": left("rph", "hour_requests"),
        "requests_left_day": left("rpd", "day_requests"),
        "tokens_left_minute": left("tpm", "minute_tokens"),
        "tokens_left_hour": left("tph", "hour_tokens"),
        "tokens_left_day": left("tpd", "day_tokens"),
        "used_requests_day": int(src.get("day_requests") or 0),
        "used_tokens_day": int(src.get("day_tokens") or 0),
        "last_tps": usage.get("last_tps"),
        "last_latency_ms": usage.get("last_latency_ms"),
        "shared_quota": shared,
    }

    # Trial credit dollar budgets — not tracked as tokens unless tpd set
    credit = (model.get("provider_limits") or {}).get("credit_usd")
    if credit is not None:
        out["credit_usd"] = credit
    tokens_total = (model.get("provider_limits") or {}).get("tokens_total") or (
        model.get("provider_limits") or {}
    ).get("tokens_per_model")
    if tokens_total is not None:
        used_life = int(src.get("lifetime_tokens") or 0)
        out["tokens_left_total"] = max(0, int(tokens_total) - used_life)
        out["tokens_total_budget"] = int(tokens_total)

    neurons = (model.get("provider_limits") or {}).get("neurons_per_day")
    if neurons is not None:
        # Rough: treat 1 token ≈ 1 neuron for inventory visibility (approximate).
        out["neurons_left_day"] = max(0, int(neurons) - int(src.get("day_tokens") or 0))

    return out


def default_store_path() -> Path:
    return Path(__file__).resolve().parent.parent / "state" / "usage.json"
