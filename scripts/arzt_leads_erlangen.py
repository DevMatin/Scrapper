#!/usr/bin/env python3
"""Ärzte in Erlangen – Google Maps + Gelbe Seiten, mit Website & E-Mail."""

from __future__ import annotations

import csv
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
GELBE_SEITEN_URL = "https://www.gelbeseiten.de/branchen/arzt/erlangen"
ERLANGEN_PLZ = re.compile(r"910\d{2}")
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
SKIP_EMAIL_DOMAINS = {
    "example.com", "domain.com", "sentry.io", "wixpress.com", "google.com",
    "facebook.com", "ingest.sentry.io", "2x.webp", "3x.webp",
}
SKIP_EMAIL_PATTERNS = ("noreply", "no-reply", "datenschutz", "sentry", "wixpress", "@o38419.", "doctolib.de")
GOOGLE_QUERIES = [
    "Arzt in Erlangen",
    "Allgemeinmediziner Erlangen",
    "Hausarzt Erlangen",
    "Facharzt Erlangen",
]


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


def is_valid_email(email: str) -> bool:
    email = email.lower().strip()
    if "@" not in email or any(p in email for p in SKIP_EMAIL_PATTERNS):
        return False
    domain = email.split("@")[-1]
    if domain in SKIP_EMAIL_DOMAINS or "." not in domain:
        return False
    return not email.endswith((".png", ".jpg", ".gif", ".webp", ".svg"))


def parse_gelbeseiten(html: str) -> list[dict]:
    parts = re.split(r'<article class="mod mod-Treffer"', html)
    leads: list[dict] = []

    for part in parts[1:]:
        m = re.search(r'<h2[^>]*class="[^"]*mod-Treffer__name[^"]*"[^>]*>([^<]+)', part)
        name = unescape(m.group(1).strip()) if m else None
        if not name:
            continue

        m = re.search(r'class="mod-Treffer--besteBranche"[^>]*>([^<]+)', part)
        branche = unescape(m.group(1).strip()) if m else "Arzt"

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
            if any(x in link for x in ("gelbeseiten", "google.", "facebook", "apple.com", "dastelefonbuch", "dasoertliche", "jameda")):
                continue
            if re.search(r">\s*Web", part[max(0, part.find(link) - 20) : part.find(link) + 80], re.I):
                website = link
                break

        email = None
        em = re.search(r'"email"\s*:\s*"([^"]+@[^"]+)"', part)
        if em and is_valid_email(em.group(1)):
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
            "branche": branche,
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
            "Scrapling mit Browser-Extras nötig: pip install 'scrapling[fetchers]' && scrapling install"
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


def fetch_google_places(api_key: str, queries: list[str], max_pages: int = 3) -> list[dict]:
    seen: set[str] = set()
    places: list[dict] = []

    for query in queries:
        page_token = None
        for _ in range(max_pages):
            result = search_places(api_key, query, page_token)
            for place in result.get("places", []):
                name = place.get("displayName", {}).get("text", "")
                key = normalize_name(name)
                if key and key not in seen:
                    seen.add(key)
                    places.append(place)
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
    branche = next(
        (t for t in types if t not in {"point_of_interest", "establishment", "health", "doctor"}),
        "Arzt",
    )

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


def fetch_email_from_website(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read(500_000).decode(errors="ignore")
    except Exception:
        return None

    for match in EMAIL_RE.findall(html):
        email = match.lower()
        if is_valid_email(email):
            return email
    return None


def build_gs_index(gs_leads: list[dict]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for lead in gs_leads:
        index[normalize_name(lead["name"])] = lead
    return index


def match_gs(lead: dict, gs_index: dict[str, dict]) -> dict | None:
    key = normalize_name(lead["name"])
    match = gs_index.get(key)
    if match:
        return match
    phone_key = normalize_phone(lead.get("telefon"))
    if phone_key:
        return next(
            (v for v in gs_index.values() if normalize_phone(v.get("telefon")) == phone_key),
            None,
        )
    return None


def merge_leads(google_leads: list[dict], gs_leads: list[dict], scrape_emails: bool = False) -> list[dict]:
    gs_index = build_gs_index(gs_leads)
    merged: dict[str, dict] = {}

    for lead in google_leads + gs_leads:
        if not is_erlangen(lead):
            continue

        key = normalize_name(lead["name"])
        if not key:
            continue

        if key not in merged:
            merged[key] = lead.copy()
        else:
            existing = merged[key]
            for field in ("telefon", "adresse", "ort", "website", "email", "branche"):
                if not existing.get(field) and lead.get(field):
                    existing[field] = lead[field]
            if existing.get("quelle") != lead.get("quelle"):
                existing["quelle"] = f"{existing['quelle']} + {lead['quelle']}"
            existing["hat_website"] = bool(existing.get("website"))

        match = match_gs(merged[key], gs_index)
        if match:
            if not merged[key].get("email") and match.get("email"):
                merged[key]["email"] = match["email"]
            if not merged[key].get("website") and match.get("website"):
                merged[key]["website"] = match["website"]
                merged[key]["hat_website"] = True

    results = list(merged.values())

    if scrape_emails:
        for lead in results:
            if not lead.get("email") and lead.get("website"):
                email = fetch_email_from_website(lead["website"])
                if email:
                    lead["email"] = email
                    lead["quelle"] = f"{lead['quelle']} + Website"

    return sorted(results, key=lambda x: x["name"].lower())


def export_csv(leads: list[dict], path: Path) -> None:
    fields = ["name", "branche", "adresse", "telefon", "email", "website", "hat_website", "quelle"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)


def main() -> int:
    load_env()

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    html_file = sys.argv[1] if len(sys.argv) > 1 else None
    scrape_emails = "--scrape-emails" in sys.argv

    if not api_key:
        print("Fehlende Umgebungsvariable: GOOGLE_MAPS_API_KEY")
        return 1

    out_dir = Path(__file__).resolve().parents[1] / "output"
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / "aerzte_erlangen.csv"

    print("→ Gelbe Seiten …")
    if html_file and not html_file.startswith("--"):
        html = Path(html_file).read_text()
    else:
        html = fetch_gelbeseiten_html()

    gs_all = parse_gelbeseiten(html)
    gs_filtered = [l for l in gs_all if is_erlangen(l)]
    print(f"  {len(gs_all)} Treffer | {len(gs_filtered)} in Erlangen")

    print("→ Google Maps …")
    places = fetch_google_places(api_key, GOOGLE_QUERIES)
    google_all = [place_to_lead(p) for p in places]
    google_filtered = [l for l in google_all if is_erlangen(l)]
    print(f"  {len(places)} unique | {len(google_filtered)} in Erlangen")

    leads = merge_leads(google_filtered, gs_filtered, scrape_emails=scrape_emails)
    with_website = [l for l in leads if l.get("website")]
    with_email = [l for l in leads if l.get("email")]

    export_csv(leads, csv_path)

    print(f"\nGesamt: {len(leads)} Ärzte in Erlangen")
    print(f"  Mit Website: {len(with_website)}")
    print(f"  Mit E-Mail:  {len(with_email)}")
    print(f"  CSV: {csv_path}\n")

    for lead in leads:
        web = lead.get("website") or "-"
        email = lead.get("email") or "-"
        print(f"  {lead['name']}")
        print(f"    Tel: {lead.get('telefon') or '-'} | E-Mail: {email}")
        print(f"    Web: {web}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
