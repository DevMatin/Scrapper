#!/usr/bin/env python3
"""Batch SEO scan for leads with websites (Supabase or CSV)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from scrapling.integrations.claude_seo.config import load_env
from scrapling.integrations.claude_seo.orchestrator.lead_batch import scan_leads


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch SEO scan for leads")
    parser.add_argument("--csv", type=Path, help="CSV with website column")
    parser.add_argument("--supabase", action="store_true", help="Load leads from Supabase")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args()
    load_env()

    leads: list[dict] = []
    if args.csv:
        leads = load_csv(args.csv)
    elif args.supabase:
        from scrapling.integrations.claude_seo.supabase_store import fetch_leads_with_websites

        leads = fetch_leads_with_websites(limit=args.limit)
    else:
        print("Provide --csv or --supabase", file=sys.stderr)
        return 2

    results = scan_leads(leads, persist=not args.no_persist)
    if args.json:
        json.dump(results, sys.stdout, indent=2, ensure_ascii=False, default=str)
        sys.stdout.write("\n")
    else:
        print(f"Scanned {len(results)} websites")
    return 0


if __name__ == "__main__":
    sys.exit(main())
