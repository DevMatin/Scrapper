from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Literal

from scrapling.integrations.claude_seo.config import load_env

WebsiteFilter = Literal["with", "without", "all"]

FIELD_MASK = (
    "places.displayName,places.formattedAddress,places.nationalPhoneNumber,"
    "places.websiteUri,places.types,nextPageToken"
)


def _api_request(url: str, data: dict | None = None, headers: dict | None = None) -> dict:
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def search_places(api_key: str, query: str, page_token: str | None = None) -> dict:
    payload: dict = {
        "textQuery": query,
        "languageCode": "de",
        "maxResultCount": 20,
    }
    if page_token:
        payload["pageToken"] = page_token

    return _api_request(
        "https://places.googleapis.com/v1/places:searchText",
        payload,
        {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
    )


def fetch_all_places(api_key: str, query: str, max_pages: int = 3) -> list[dict]:
    places: list[dict] = []
    page_token = None

    for _ in range(max_pages):
        result = search_places(api_key, query, page_token)
        places.extend(result.get("places", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return places


def place_to_lead(place: dict, quelle: str = "Google Maps") -> dict:
    name = place.get("displayName", {}).get("text", "")
    adresse = place.get("formattedAddress")
    telefon = place.get("nationalPhoneNumber")
    website = place.get("websiteUri")
    types = place.get("types") or []
    branche = next((t for t in types if t not in {"point_of_interest", "establishment"}), None)

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
        "quelle": quelle,
    }


def filter_places(places: list[dict], website_filter: WebsiteFilter) -> list[dict]:
    if website_filter == "all":
        return places
    if website_filter == "with":
        return [p for p in places if p.get("websiteUri")]
    return [p for p in places if not p.get("websiteUri")]


def _supabase_headers(key: str, *, prefer: str | None = None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def lead_exists(supabase_url: str, supabase_key: str, lead: dict) -> bool:
    return fetch_lead_id(supabase_url, supabase_key, lead) is not None


def fetch_lead_id(supabase_url: str, supabase_key: str, lead: dict) -> str | None:
    name = urllib.parse.quote(lead.get("name") or "", safe="")
    ort = lead.get("ort")
    params = [f"name=eq.{name}"]
    if ort:
        params.append(f"ort=eq.{urllib.parse.quote(ort, safe='')}")
    website = lead.get("website")
    if website:
        params.append(f"website=eq.{urllib.parse.quote(website, safe='')}")
    query = f"{supabase_url.rstrip('/')}/rest/v1/leads?select=id&{'&'.join(params)}&limit=1"
    req = urllib.request.Request(
        query,
        headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            rows = json.loads(resp.read().decode())
            if rows:
                return rows[0].get("id")
    except urllib.error.HTTPError:
        pass
    return None


def resolve_lead_ids(
    supabase_url: str,
    supabase_key: str,
    leads: list[dict],
) -> list[dict]:
    resolved: list[dict] = []
    for lead in leads:
        if lead.get("id"):
            resolved.append(lead)
            continue
        lead_id = fetch_lead_id(supabase_url, supabase_key, lead)
        if lead_id:
            resolved.append({**lead, "id": lead_id})
        else:
            resolved.append(lead)
    return resolved


def save_leads(
    supabase_url: str,
    supabase_key: str,
    leads: list[dict],
    *,
    skip_duplicates: bool = True,
) -> list[dict]:
    if not leads:
        return []

    to_insert: list[dict] = []
    for lead in leads:
        if skip_duplicates and lead_exists(supabase_url, supabase_key, lead):
            continue
        to_insert.append(lead)

    if not to_insert:
        return []

    url = f"{supabase_url.rstrip('/')}/rest/v1/leads"
    req = urllib.request.Request(
        url,
        data=json.dumps(to_insert).encode(),
        method="POST",
        headers=_supabase_headers(supabase_key, prefer="return=representation"),
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_leads_for_query(
    query: str,
    *,
    limit: int = 10,
    website_filter: WebsiteFilter = "with",
    max_pages: int = 3,
) -> list[dict]:
    load_env()
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not configured")

    places = fetch_all_places(api_key, query, max_pages=max_pages)
    filtered = filter_places(places, website_filter)
    return [place_to_lead(p) for p in filtered[:limit]]


def fetch_and_save_leads(
    query: str,
    *,
    limit: int = 10,
    website_filter: WebsiteFilter = "with",
    skip_duplicates: bool = True,
) -> list[dict]:
    load_env()
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY required")

    leads = fetch_leads_for_query(query, limit=limit, website_filter=website_filter)
    return save_leads(supabase_url, supabase_key, leads, skip_duplicates=skip_duplicates)
