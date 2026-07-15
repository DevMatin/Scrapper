#!/usr/bin/env python3
"""Cafés ohne Website aber mit E-Mail – Google Maps + Gelbe Seiten."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

FIELD_MASK = (
    "places.displayName,places.formattedAddress,places.nationalPhoneNumber,"
    "places.websiteUri,places.types,nextPageToken"
)
GELBE_SEITEN_URL = "https://www.gelbeseiten.de/branchen/caf%C3%A9/erlangen"
ERLANGEN_PLZ = re.compile(r"910\d{2}")


def load_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def api_request(url: str, data: dict | None = None, headers: dict | None = None) -> dict:
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def normalize_name(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9äöüß]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_phone(phone: str | None) -> str:
    if not phone:
        return ""
    return re.sub(r"\D", "", phone)[-8:]


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def clean_text(text: str) -> str:
    text = re.sub(r'<span[^>]*class="[^"]*entfernung[^"]*"[^>]*>.*?</span>', "", text, flags=re.S)
    return unescape(re.sub(r"\s+", " ", strip_html(text))).strip()


def parse_gelbeseiten(html: str) -> list[dict]:
    parts = re.split(r'<article class="mod mod-Treffer"', html)
    leads: list[dict] = []

    for part in parts[1:]:
        m = re.search(r'<h2[^>]*class="[^"]*mod-Treffer__name[^"]*"[^>]*>([^<]+)', part)
        name = unescape(m.group(1).strip()) if m else None
        if not name:
            continue

        m = re.search(r'class="mod-Treffer--besteBranche"[^>]*>([^<]+)', part)
        branche = unescape(m.group(1).strip()) if m else None

        m = re.search(r'class="mod-AdresseKompakt__adress-text"[^>]*>(.*?)</div>', part, re.S)
        adresse = clean_text(m.group(1)) if m else None

        telefon = None
        pm = re.search(r'"phones"\s*:\s*\[\s*"([^"]+)"', part)
        if pm:
            telefon = pm.group(1).strip()
        else:
            m = re.search(r'href="tel:([^"]+)"', part)
            telefon = unescape(m.group(1).strip()) if m else None

        website = None
        for link in re.findall(r'href="(https?://[^"]+)"', part):
            if any(x in link for x in ("gelbeseiten", "google.", "facebook", "apple.com", "dastelefonbuch", "dasoertliche")):
                continue
            if re.search(r">\s*Web", part[part.find(link) - 20 : part.find(link) + 80], re.I):
                website = link
                break

        email = None
        em = re.search(r'"email"\s*:\s*"([^"]+@[^"]+)"', part)
        if em:
            email = em.group(1).lower()

        ort = None
        if adresse:
            cm = re.search(r"(\d{5}\s+[^,]+)", adresse)
            if cm:
                ort = cm.group(1).strip()

        leads.append({
            "name": name,
            "adresse": adresse,
            "telefon": telefon,
            "branche": branche or "café",
            "ort": ort,
            "website": website,
            "hat_website": bool(website),
            "email": email,
            "quelle": "Gelbe Seiten",
        })

    return leads


def fetch_gelbeseiten_html() -> str:
    try:
        from scrapling.fetchers import DynamicFetcher
    except ImportError as exc:
        raise RuntimeError(
            "Scrapling mit Browser-Extras nötig für Gelbe Seiten: pip install 'scrapling[fetchers]' && scrapling install"
        ) from exc

    page = DynamicFetcher.fetch(
        GELBE_SEITEN_URL,
        headless=True,
        network_idle=True,
        wait_selector="article.mod-Treffer",
        wait_selector_state="visible",
        locale="de-DE",
        timeout=60000,
    )
    return page.body.decode() if isinstance(page.body, bytes) else str(page.body)


def search_places(api_key: str, query: str, page_token: str | None = None) -> dict:
    payload: dict = {"textQuery": query, "languageCode": "de", "maxResultCount": 20}
    if page_token:
        payload["pageToken"] = page_token

    return api_request(
        "https://places.googleapis.com/v1/places:searchText",
        payload,
        {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
    )


def fetch_google_places(api_key: str, query: str, max_pages: int = 3) -> list[dict]:
    places: list[dict] = []
    page_token = None

    for _ in range(max_pages):
        result = search_places(api_key, query, page_token)
        places.extend(result.get("places", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return places


def place_to_lead(place: dict) -> dict:
    name = place.get("displayName", {}).get("text", "")
    adresse = place.get("formattedAddress")
    telefon = place.get("nationalPhoneNumber")
    website = place.get("websiteUri")
    types = place.get("types") or []
    branche = next((t for t in types if t not in {"point_of_interest", "establishment", "food", "store"}), "café")

    ort = None
    if adresse:
        parts = [p.strip() for p in adresse.split(",")]
        if len(parts) >= 2:
            ort = parts[-2]

    return {
        "name": name,
        "adresse": adresse,
        "telefon": telefon,
        "branche": branche,
        "ort": ort,
        "website": website,
        "hat_website": bool(website),
        "email": None,
        "quelle": "Google Maps",
    }


def is_erlangen(lead: dict) -> bool:
    blob = " ".join(filter(None, [lead.get("adresse"), lead.get("ort")]))
    return bool(ERLANGEN_PLZ.search(blob)) or "erlangen" in blob.lower()


def enrich_google_with_gelbeseiten(google_leads: list[dict], gs_index: dict[str, dict]) -> list[dict]:
    enriched: list[dict] = []
    for lead in google_leads:
        key = normalize_name(lead["name"])
        phone_key = normalize_phone(lead.get("telefon"))
        match = gs_index.get(key)
        if not match and phone_key:
            match = next((v for k, v in gs_index.items() if normalize_phone(v.get("telefon")) == phone_key), None)
        if match and match.get("email"):
            lead = {**lead, "email": match["email"]}
        enriched.append(lead)
    return enriched


def build_gs_index(gs_leads: list[dict]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for lead in gs_leads:
        index[normalize_name(lead["name"])] = lead
    return index


def merge_leads(*groups: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for group in groups:
        for lead in group:
            if not lead.get("email") or lead.get("hat_website"):
                continue
            if not is_erlangen(lead):
                continue
            key = f"{normalize_name(lead['name'])}|{lead['email']}"
            if key not in merged:
                merged[key] = lead
                continue
            existing = merged[key]
            if existing.get("quelle") != lead.get("quelle"):
                existing["quelle"] = f"{existing['quelle']} + {lead['quelle']}"
            for field in ("telefon", "adresse", "ort", "branche"):
                if not existing.get(field) and lead.get(field):
                    existing[field] = lead[field]
    return list(merged.values())


def fetch_existing_keys(supabase_url: str, supabase_key: str) -> set[str]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/leads?select=name,email"
    req = urllib.request.Request(
        url,
        headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        rows = json.loads(resp.read().decode())
    return {f"{normalize_name(r['name'])}|{(r.get('email') or '').lower()}" for r in rows}


def save_leads(supabase_url: str, supabase_key: str, leads: list[dict]) -> list[dict]:
    if not leads:
        return []

    url = f"{supabase_url.rstrip('/')}/rest/v1/leads"
    body = json.dumps(leads).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Prefer": "return=representation",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    load_env()

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    query = sys.argv[1] if len(sys.argv) > 1 else "Café in Erlangen"
    html_file = sys.argv[2] if len(sys.argv) > 2 else None

    missing = [k for k, v in {
        "GOOGLE_MAPS_API_KEY": api_key,
        "SUPABASE_URL": supabase_url,
        "SUPABASE_KEY": supabase_key,
    }.items() if not v]
    if missing:
        print(f"Fehlende Umgebungsvariablen: {', '.join(missing)}")
        return 1

    print("→ Gelbe Seiten …")
    if html_file:
        html = Path(html_file).read_text()
    else:
        html = fetch_gelbeseiten_html()

    gs_all = parse_gelbeseiten(html)
    gs_filtered = [l for l in gs_all if not l["hat_website"] and l["email"] and is_erlangen(l)]
    print(f"  {len(gs_all)} Treffer | {len(gs_filtered)} Erlangen ohne Website mit E-Mail")

    print("→ Google Maps …")
    places = fetch_google_places(api_key, query)
    google_all = [place_to_lead(p) for p in places if not p.get("websiteUri")]
    gs_index = build_gs_index(gs_all)
    google_enriched = enrich_google_with_gelbeseiten(google_all, gs_index)
    google_filtered = [l for l in google_enriched if l.get("email") and is_erlangen(l)]
    print(f"  {len(places)} Treffer | {len(google_all)} ohne Website | {len(google_filtered)} mit E-Mail (via Gelbe Seiten)")

    leads = merge_leads(gs_filtered, google_filtered)
    existing = fetch_existing_keys(supabase_url, supabase_key)
    new_leads = [l for l in leads if f"{normalize_name(l['name'])}|{l['email']}" not in existing]

    print(f"\nGesamt unique: {len(leads)} | Neu: {len(new_leads)}")

    if not new_leads:
        print("Keine neuen Leads.")
        for lead in leads[:15]:
            print(f"  - {lead['name']} | {lead['email']} | {lead['quelle']}")
        return 0

    saved = save_leads(supabase_url, supabase_key, new_leads)
    print(f"Gespeichert: {len(saved)}")
    for lead in saved:
        print(f"  - {lead['name']} | {lead['email']} | {lead.get('telefon') or '-'} | {lead['quelle']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
