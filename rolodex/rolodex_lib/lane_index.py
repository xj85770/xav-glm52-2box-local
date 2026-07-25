"""Full lane → rolodex index (all catalog models, keyed + unkeyed)."""

from __future__ import annotations

from typing import Any

from .catalog import iter_models, load_catalog
from .lanes import LANE_ALIASES, LANE_DOCS, LANE_NAMES, resolve_lane
from .quota import QuotaStore, default_store_path, remaining_for_model
from .runtime import model_available


def build_lane_rolodex(
    *,
    environ: dict[str, str] | None = None,
    catalog: dict[str, Any] | None = None,
    store: QuotaStore | None = None,
) -> dict[str, Any]:
    """Return every lane with its full model rolodex (ready + missing-key cards)."""
    cat = catalog if catalog is not None else load_catalog()
    qs = store or QuotaStore(default_store_path())
    lanes: dict[str, dict[str, Any]] = {}

    for lane in LANE_NAMES:
        short = lane.split("/", 1)[1]
        cards: list[dict[str, Any]] = []
        for model in iter_models(cat):
            if short not in (model.get("lanes") or []):
                continue
            ready = model_available(model, environ)
            usage = qs.get_model(model["id"])
            rem = remaining_for_model(model, usage, qs.get_provider(str(model.get("provider_id"))))
            order = int((model.get("order_in_lane") or {}).get(short, 50))
            cards.append(
                {
                    "id": model["id"],
                    "display": model.get("display"),
                    "provider": model.get("provider_id"),
                    "tier": model.get("tier"),
                    "ready": ready,
                    "requires_env": model.get("provider_requires_env") or model.get("api_key_env"),
                    "order": order,
                    "context": model.get("context"),
                    "tps_typical": model.get("tps_typical"),
                    "tps_observed": rem.get("last_tps"),
                    "rpm": model.get("rpm"),
                    "rpd": model.get("rpd"),
                    "tpm": model.get("tpm"),
                    "tpd": model.get("tpd"),
                    "tokens_left_day": rem.get("tokens_left_day")
                    if rem.get("tokens_left_day") is not None
                    else rem.get("tokens_left_total"),
                    "requests_left_day": rem.get("requests_left_day"),
                }
            )
        cards.sort(key=lambda c: (c["order"], c["id"]))
        ready_ids = [c["id"] for c in cards if c["ready"]]
        lanes[lane] = {
            "id": lane,
            "aliases": sorted(a for a, t in LANE_ALIASES.items() if t == lane),
            "description": LANE_DOCS[lane],
            "card_count": len(cards),
            "ready_count": len(ready_ids),
            "ready_ids": ready_ids,
            "missing_key_ids": [c["id"] for c in cards if not c["ready"]],
            "cards": cards,
        }

    return {
        "lanes": lanes,
        "aliases": dict(LANE_ALIASES),
        "how_to": {
            "list_lanes": "GET /v1/lanes  or  model=lanes",
            "use_lane": "model=lane/smart  (or alias: smart / local / fast / code)",
            "use_exact_card": "model=or/qwen3-coder  (any card id from a lane rolodex)",
        },
    }


def render_lanes_markdown(index: dict[str, Any]) -> str:
    lines = [
        "# Rolodex lanes",
        "",
        "Type a **lane** to auto-swap across its populated cards, or an exact **card id**.",
        "",
    ]
    for lane_name in LANE_NAMES:
        lane = index["lanes"][lane_name]
        lines.append(f"## `{lane_name}`  ({lane['ready_count']}/{lane['card_count']} ready)")
        lines.append("")
        lines.append(lane["description"])
        lines.append(f"Aliases: {', '.join(f'`{a}`' for a in lane['aliases'])}")
        lines.append("")
        lines.append("| order | ready | id | display | ctx | t/s | rpd | tok left/day | key |")
        lines.append("|---:|---|---|---|---:|---:|---:|---:|---|")
        for c in lane["cards"]:
            ready = "YES" if c["ready"] else "no-key"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(c["order"]),
                        ready,
                        f"`{c['id']}`",
                        str(c.get("display") or ""),
                        "" if c.get("context") is None else str(c["context"]),
                        "" if c.get("tps_typical") is None else str(c["tps_typical"]),
                        "" if c.get("rpd") is None else str(c["rpd"]),
                        "" if c.get("tokens_left_day") is None else str(c["tokens_left_day"]),
                        str(c.get("requires_env") or "—"),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines)


def resolve_model_target(name: str) -> str:
    """Normalize user-typed model to lane id, 'lanes', or passthrough card id."""
    key = (name or "").strip()
    if key in {"lanes", "lane", "rolodex", "rolodex/lanes"}:
        return "lanes"
    try:
        return resolve_lane(key)
    except KeyError:
        return key
