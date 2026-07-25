"""LiteLLM custom logger → local quota store (tokens left / last t/s)."""

from __future__ import annotations

from typing import Any

from litellm.integrations.custom_logger import CustomLogger

from .quota import QuotaStore, default_store_path

_store: QuotaStore | None = None


def _get_store() -> QuotaStore:
    global _store
    if _store is None:
        _store = QuotaStore(default_store_path())
    return _store


def _extract_ids(kwargs: dict[str, Any]) -> tuple[str, str]:
    litellm_params = kwargs.get("litellm_params") or {}
    meta = litellm_params.get("metadata") or {}
    model_info = meta.get("model_info") or {}
    model_id = model_info.get("id") or kwargs.get("model") or litellm_params.get("model_info", {}).get("id")
    provider_id = model_info.get("provider") or "unknown"
    if not model_id:
        model_id = kwargs.get("model") or "unknown"
    # Prefer catalog id from model_info attached at deploy time
    mi = litellm_params.get("model_info") or {}
    if isinstance(mi, dict) and mi.get("id"):
        model_id = mi["id"]
        provider_id = mi.get("provider") or provider_id
    return str(model_id), str(provider_id)


class lanes2UsageLogger(CustomLogger):
    def log_success_event(self, kwargs, response_obj, start_time, end_time):  # noqa: ANN001
        try:
            model_id, provider_id = _extract_ids(kwargs)
            usage = getattr(response_obj, "usage", None)
            prompt = int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
            completion = int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0
            latency_ms = None
            tps = None
            try:
                latency_ms = (end_time - start_time).total_seconds() * 1000.0
                if completion > 0 and latency_ms > 0:
                    tps = completion / (latency_ms / 1000.0)
            except Exception:
                pass
            _get_store().record(
                model_id=model_id,
                provider_id=provider_id,
                prompt_tokens=prompt,
                completion_tokens=completion,
                latency_ms=latency_ms,
                tps=tps,
            )
        except Exception:
            return

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):  # noqa: ANN001
        self.log_success_event(kwargs, response_obj, start_time, end_time)


proxy_handler_instance = lanes2UsageLogger()


def usage_callback(kwargs, completion_response, start_time, end_time):  # noqa: ANN001
    """Optional functional callback for non-proxy Router usage."""
    proxy_handler_instance.log_success_event(kwargs, completion_response, start_time, end_time)
