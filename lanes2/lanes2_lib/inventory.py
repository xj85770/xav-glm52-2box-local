"""Inventory views: model name, context, limits, t/s, tokens left — for humans & agent context."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import iter_models, load_catalog
from .quota import QuotaStore, default_store_path, remaining_for_model
from .runtime import model_available


def build_inventory(
    *,
    environ: dict[str, str] | None = None,
    catalog: dict[str, Any] | None = None,
    store: QuotaStore | None = None,
    only_available: bool = False,
) -> list[dict[str, Any]]:
    cat = catalog if catalog is not None else load_catalog()
    qs = store or QuotaStore(default_store_path())
    rows: list[dict[str, Any]] = []
    for model in iter_models(cat):
        available = model_available(model, environ)
        if only_available and not available:
            continue
        usage = qs.get_model(model["id"])
        provider_usage = qs.get_provider(str(model.get("provider_id")))
        rem = remaining_for_model(model, usage, provider_usage)
        observed_tps = rem.get("last_tps")
        rows.append(
            {
                "id": model["id"],
                "display": model.get("display"),
                "provider": model.get("provider_id"),
                "provider_name": model.get("provider_name"),
                "tier": model.get("tier"),
                "privacy": model.get("privacy"),
                "available": available,
                "requires_env": model.get("provider_requires_env") or model.get("api_key_env"),
                "lanes": model.get("lanes") or [],
                "litellm_model": model.get("litellm_model"),
                "context": model.get("context"),
                "context_note": model.get("context_note"),
                "tps_typical": model.get("tps_typical"),
                "tps_note": model.get("tps_note"),
                "tps_observed": observed_tps,
                "limits": {
                    "rpm": model.get("rpm"),
                    "rpd": model.get("rpd"),
                    "rph": model.get("rph"),
                    "tpm": model.get("tpm"),
                    "tpd": model.get("tpd"),
                    "tph": model.get("tph"),
                    "provider": model.get("provider_limits") or {},
                },
                "remaining": rem,
                "notes": model.get("provider_notes") or "",
            }
        )
    rows.sort(key=lambda r: (not r["available"], r.get("tier") or "", r.get("provider") or "", r["id"]))
    return rows


def render_markdown(rows: list[dict[str, Any]], *, title: str = "lanes2 inventory") -> str:
    lines = [
        f"# {title}",
        "",
        "Swap by **model id** (exact) or by **lane** (`lane/local|fast|smart|code`).",
        "Limits from [free-llm-api-resources](https://github.com/cheahjs/free-llm-api-resources). "
        "`tokens_left_*` / `requests_left_*` are local budget remaining vs published free caps "
        "(not live provider dashboards).",
        "",
        "| ready | id | display | provider | tier | ctx | t/s typ | t/s obs | rpm | rpd | tpm | tpd | req left/day | tok left/day | lanes |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        rem = r["remaining"]
        lim = r["limits"]
        ready = "YES" if r["available"] else "no-key"
        ctx = r.get("context") if r.get("context") is not None else ""
        tps_t = r.get("tps_typical") if r.get("tps_typical") is not None else ""
        tps_o = f"{r['tps_observed']:.1f}" if isinstance(r.get("tps_observed"), (int, float)) else ""
        def fmt(v: Any) -> str:
            return "" if v is None else str(v)

        lines.append(
            "| "
            + " | ".join(
                [
                    ready,
                    f"`{r['id']}`",
                    str(r.get("display") or ""),
                    str(r.get("provider") or ""),
                    str(r.get("tier") or ""),
                    fmt(ctx),
                    fmt(tps_t),
                    tps_o,
                    fmt(lim.get("rpm")),
                    fmt(lim.get("rpd")),
                    fmt(lim.get("tpm")),
                    fmt(lim.get("tpd")),
                    fmt(rem.get("requests_left_day")),
                    fmt(rem.get("tokens_left_day") if rem.get("tokens_left_day") is not None else rem.get("tokens_left_total")),
                    ",".join(r.get("lanes") or []),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Notes", ""])
    seen: set[str] = set()
    for r in rows:
        key = str(r.get("provider"))
        if key in seen:
            continue
        seen.add(key)
        note = (r.get("notes") or "").strip()
        if note:
            lines.append(f"- **{r.get('provider_name')}** (`{key}`): {note}")
    lines.append("")
    return "\n".join(lines)


def write_agent_context(
    out_path: Path | None = None,
    *,
    environ: dict[str, str] | None = None,
    only_available: bool = False,
) -> Path:
    root = Path(__file__).resolve().parent.parent
    out = out_path or (root / "state" / "AGENT_CONTEXT.md")
    rows = build_inventory(environ=environ, only_available=only_available)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_markdown(rows), encoding="utf-8")
    json_path = out.with_suffix(".json")
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return out
