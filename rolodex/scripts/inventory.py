#!/usr/bin/env python3
"""Print / refresh the rolodex inventory (model, context, limits, t/s, tokens left)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from rolodex_lib.inventory import build_inventory, render_markdown, write_agent_context


def main() -> int:
    parser = argparse.ArgumentParser(description="Rolodex model inventory")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--available", action="store_true", help="Only models with keys configured")
    parser.add_argument("--write", action="store_true", help="Write state/AGENT_CONTEXT.md")
    parser.add_argument("--lane", type=str, default="", help="Filter by lane short name (fast/smart/...)")
    parser.add_argument("--provider", type=str, default="", help="Filter by provider id")
    args = parser.parse_args()

    if args.env_file.is_file():
        load_dotenv(args.env_file)

    rows = build_inventory(only_available=args.available)
    if args.lane:
        rows = [r for r in rows if args.lane in (r.get("lanes") or [])]
    if args.provider:
        rows = [r for r in rows if r.get("provider") == args.provider]

    if args.write:
        path = write_agent_context(only_available=args.available)
        print(f"wrote {path}", file=sys.stderr)

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print(render_markdown(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
