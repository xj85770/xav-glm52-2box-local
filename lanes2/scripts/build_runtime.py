#!/usr/bin/env python3
"""Build config.runtime.yaml + agent context inventory from catalog + env."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from lanes2_lib.inventory import build_inventory, write_agent_context
from lanes2_lib.runtime import build_runtime_config, summarize_runtime, write_runtime_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Build rolodex runtime config + inventory")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--out", type=Path, default=ROOT / "config.runtime.yaml")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--only-available", action="store_true", help="Agent context: keyed cards only")
    args = parser.parse_args()

    if args.env_file.is_file():
        load_dotenv(args.env_file)

    cfg = build_runtime_config()
    write_runtime_config(args.out)
    ctx = write_agent_context(only_available=args.only_available)
    summary = summarize_runtime(cfg)
    inv = build_inventory(only_available=False)
    ready = [r for r in inv if r["available"]]

    if args.json:
        print(
            json.dumps(
                {
                    "summary": summary,
                    "ready_models": len(ready),
                    "catalog_models": len(inv),
                    "agent_context": str(ctx),
                },
                indent=2,
            )
        )
    else:
        print(f"wrote {args.out}")
        print(f"wrote {ctx} (+ .json)")
        print(f"catalog models: {len(inv)}  ready (keys present): {len(ready)}  litellm cards: {summary['total_cards']}")
        for lane, ids in summary["lanes"].items():
            print(f"  {lane}: {len(ids)} model(s)")
        if "lane/local" not in summary["lanes"]:
            print("WARNING: lane/local missing")
            return 1
        if summary["total_cards"] == 0:
            print("WARNING: no cards")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
