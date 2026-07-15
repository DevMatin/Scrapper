#!/usr/bin/env python3
"""Sucht Firmen via Google Places API und speichert Leads in Supabase."""

from __future__ import annotations

import argparse
import os
import sys

from scrapling.integrations.claude_seo.config import load_env
from scrapling.integrations.claude_seo.places import (
    fetch_all_places,
    filter_places,
    place_to_lead,
    save_leads,
)


def main() -> int:
    load_env()

    parser = argparse.ArgumentParser(description="Google Places → Supabase Leads")
    parser.add_argument("query", nargs="?", default="Café in Erlangen")
    parser.add_argument("--with-website", action="store_true", help="Nur Leads mit Website")
    parser.add_argument("--without-website", action="store_true", help="Nur Leads ohne Website (Default)")
    parser.add_argument("--all", action="store_true", help="Alle Leads")
    args = parser.parse_args()

    if args.with_website:
        website_filter = "with"
    elif args.all:
        website_filter = "all"
    else:
        website_filter = "without"

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    missing = [k for k, v in {
        "GOOGLE_MAPS_API_KEY": api_key,
        "SUPABASE_URL": supabase_url,
        "SUPABASE_KEY": supabase_key,
    }.items() if not v]
    if missing:
        print(f"Fehlende Umgebungsvariablen: {', '.join(missing)}")
        return 1

    places = fetch_all_places(api_key, args.query)
    filtered = filter_places(places, website_filter)
    leads = [place_to_lead(p) for p in filtered]

    label = {"with": "Mit Website", "without": "Ohne Website", "all": "Alle"}[website_filter]
    print(f"Gefunden: {len(places)} | {label}: {len(leads)}")

    if not leads:
        print("Keine neuen Leads.")
        return 0

    saved = save_leads(supabase_url, supabase_key, leads, skip_duplicates=True)
    print(f"Gespeichert: {len(saved)}")
    for lead in saved:
        site = lead.get("website") or "-"
        print(f"  - {lead['name']} | {lead.get('ort') or '-'} | {site}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
