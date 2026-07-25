"""Load and query the free-API catalog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .lanes import LANE_NAMES


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or (_root() / "catalog.yaml")
    with cfg_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "providers" not in data:
        raise ValueError(f"invalid catalog: {cfg_path}")
    return data


def iter_models(catalog: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Flatten providers → models with provider fields attached."""
    cat = catalog if catalog is not None else load_catalog()
    out: list[dict[str, Any]] = []
    for prov in cat.get("providers", []):
        for model in prov.get("models", []) or []:
            row = {
                "provider_id": prov.get("id"),
                "provider_name": prov.get("name"),
                "tier": prov.get("tier"),
                "privacy": prov.get("privacy"),
                "provider_requires_env": prov.get("requires_env"),
                "provider_requires_env_extra": prov.get("requires_env_extra") or [],
                "provider_shared_quota": bool(prov.get("shared_quota")),
                "provider_limits": prov.get("limits") or {},
                "provider_notes": prov.get("notes") or "",
                **model,
            }
            # Inherit provider RPM if model omits
            plim = prov.get("limits") or {}
            for key in ("rpm", "rpd", "tpm", "tpd", "rph", "tph"):
                if row.get(key) is None and key in plim:
                    row[key] = plim[key]
            out.append(row)
    return out


def model_by_id(model_id: str, catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    for row in iter_models(catalog):
        if row["id"] == model_id:
            return row
    raise KeyError(model_id)


def lane_members(lane: str, catalog: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not lane.startswith("lane/"):
        lane = f"lane/{lane}"
    if lane not in LANE_NAMES:
        raise KeyError(lane)
    short = lane.split("/", 1)[1]
    members = [m for m in iter_models(catalog) if short in (m.get("lanes") or [])]
    members.sort(key=lambda m: ((m.get("order_in_lane") or {}).get(short, 99), m["id"]))
    return members
