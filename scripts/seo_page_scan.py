#!/usr/bin/env python3
"""Thin wrapper: full page SEO scan via scrapling seo integration."""

from __future__ import annotations

import argparse
import json
import sys

from scrapling.integrations.claude_seo.orchestrator.page_scan import scan_page


def main() -> int:
    parser = argparse.ArgumentParser(description="SEO page scan (claude-seo integration)")
    parser.add_argument("url")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-pagespeed", action="store_true")
    args = parser.parse_args()

    report = scan_page(args.url, include_pagespeed=not args.no_pagespeed)
    if args.json:
        json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        scores = report.get("scores") or {}
        print(f"URL: {report.get('url')}")
        print(f"Health: {scores.get('health')}/100")
        for issue in report.get("issues") or []:
            print(f"  [{issue.get('severity')}] {issue.get('title')}")
    return 0 if not report.get("error") else 1


if __name__ == "__main__":
    sys.exit(main())
