"""Lane catalog — the product surface agents should ask for."""

from __future__ import annotations

from typing import Any

LANE_NAMES: tuple[str, ...] = (
    "lane/local",
    "lane/fast",
    "lane/smart",
    "lane/code",
)

LANE_ALIASES: dict[str, str] = {
    "local": "lane/local",
    "fast": "lane/fast",
    "smart": "lane/smart",
    "code": "lane/code",
    "lane-local": "lane/local",
    "lane-fast": "lane/fast",
    "lane-smart": "lane/smart",
    "lane-code": "lane/code",
}

LANE_DOCS: dict[str, str] = {
    "lane/local": "Private local GLM (ds4 :8000 → llama.cpp :8080).",
    "lane/fast": "Burst chat: Groq → Cerebras → OpenRouter free-small.",
    "lane/smart": "Best free reasoning: Gemini → OpenRouter free-big → local.",
    "lane/code": "Coding: Codestral → Qwen-coder free → Groq gpt-oss → local.",
}


def resolve_lane(name: str) -> str:
    """Normalize alias or lane id to canonical lane/… name."""
    key = (name or "").strip()
    if key in LANE_NAMES:
        return key
    if key in LANE_ALIASES:
        return LANE_ALIASES[key]
    raise KeyError(f"unknown lane or alias: {name!r}")


def describe_lanes(runtime_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return lane summaries, optionally annotated with live card counts."""
    counts: dict[str, int] = {n: 0 for n in LANE_NAMES}
    cards: dict[str, list[str]] = {n: [] for n in LANE_NAMES}
    if runtime_config:
        for entry in runtime_config.get("model_list", []):
            lane = entry.get("model_name")
            if lane not in counts:
                continue
            counts[lane] += 1
            info = entry.get("model_info") or {}
            card_id = info.get("id") or entry.get("litellm_params", {}).get("model", "?")
            cards[lane].append(str(card_id))

    out: list[dict[str, Any]] = []
    for name in LANE_NAMES:
        out.append(
            {
                "lane": name,
                "aliases": sorted(a for a, t in LANE_ALIASES.items() if t == name),
                "description": LANE_DOCS[name],
                "cards": counts[name],
                "card_ids": cards[name],
            }
        )
    return out
