#!/usr/bin/env python3
"""Prüft Websites aus aerzte_erlangen.csv auf veraltetes Design.

Deprecated: prefer `python scripts/seo_page_scan.py <url>` or `scrapling seo page <url>`.
This script remains for backward-compatible CSV batch audits.
"""

from __future__ import annotations

import csv
import re
import ssl
import sys
import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (compatible; WebsiteAudit/1.0)"
TIMEOUT = 15
MAX_BYTES = 800_000

OLD_GENERATORS = (
    "frontpage", "dreamweaver", "golive", "microsoft word", "iweb",
    "homestead", "webs.com", "jimdo old",
)
OLD_JQUERY = re.compile(r"jquery[.-]?(1\.[0-9]|2\.[0-9])", re.I)
COPYRIGHT_YEAR = re.compile(r"(?:©|copyright|\bc)\s*(19\d{2}|20[0-1]\d)\b", re.I)
TABLE_LAYOUT = re.compile(r"<table[^>]*>.*?<table", re.I | re.S)
VIEWPORT = re.compile(r'<meta[^>]+name=["\']viewport["\']', re.I)
MEDIA_QUERY = re.compile(r"@media\s*\(", re.I)
FIXED_WIDTH = re.compile(r'\bwidth\s*[:=]\s*["\']?\s*(760|800|900|960|980|1000)\s*px', re.I)
FONT_TAG = re.compile(r"<\s*font\b", re.I)
CENTER_TAG = re.compile(r"<\s*center\b", re.I)
MARQUEE = re.compile(r"<\s*marquee\b", re.I)
FRAMES = re.compile(r"<\s*(frameset|frame)\b", re.I)
FLASH = re.compile(r"\.swf\b|application/x-shockwave-flash", re.I)
HTML4 = re.compile(r"<!DOCTYPE\s+HTML\s+4|XHTML\s+1\.[01]", re.I)
IE_ONLY = re.compile(r"X-UA-Compatible|<!--\[if\s+IE", re.I)
BLINK = re.compile(r"<\s*blink\b|text-decoration\s*:\s*blink", re.I)
BUILDER_OLD = re.compile(r"wix\.com|jimdo\.com|homepage-baukasten|webnode", re.I)


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        parsed = urlparse(f"https://{url.strip()}")
    query_items = parse_qsl(parsed.query, keep_blank_values=False)
    cleaned_query = urlencode([
        (k, v) for k, v in query_items
        if not k.lower().startswith("utm_") and k.lower() not in {"gclid", "fbclid"}
    ])
    path = parsed.path or "/"
    return urlunparse((parsed.scheme, parsed.netloc, path, "", cleaned_query, ""))


def candidate_urls(url: str) -> list[str]:
    base = normalize_url(url)
    parsed = urlparse(base)
    root = urlunparse((parsed.scheme, parsed.netloc, "/", "", "", ""))
    no_query = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    variants = [base, no_query, root]
    if parsed.scheme == "https":
        variants.extend([base.replace("https://", "http://", 1), root.replace("https://", "http://", 1)])
    elif parsed.scheme == "http":
        variants.extend([base.replace("http://", "https://", 1), root.replace("http://", "https://", 1)])

    unique: list[str] = []
    seen: set[str] = set()
    for item in variants:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def fetch_once(url: str, use_unverified_ssl: bool = False) -> tuple[str | None, str | None, int | str]:
    ctx = ssl._create_unverified_context() if use_unverified_ssl else ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            final_url = resp.geturl()
            status = resp.status
            raw = resp.read(MAX_BYTES)
            charset = "utf-8"
            ct = resp.headers.get_content_charset()
            if ct:
                charset = ct
            html = raw.decode(charset, errors="ignore")
            return html, final_url, status
    except urllib.error.HTTPError as exc:
        try:
            html = exc.read(MAX_BYTES).decode("utf-8", errors="ignore")
            return html, url, exc.code
        except Exception:
            return None, url, exc.code
    except Exception as exc:
        return None, url, str(exc)


def fetch(url: str) -> tuple[str | None, str | None, int | str]:
    last_error: int | str = "unbekannt"
    for candidate in candidate_urls(url):
        for attempt in range(2):
            html, final_url, status = fetch_once(candidate, use_unverified_ssl=(attempt == 1))
            if html is not None:
                return html, final_url, status
            last_error = status
            time.sleep(0.35)
    return None, url, last_error


def audit_website(url: str) -> dict:
    if not url or not url.strip():
        return {"fehler": "keine Website", "score": 0, "probleme": "", "empfehlung": ""}

    url = url.strip()
    html, final_url, status = fetch(url)

    if html is None:
        return {
            "fehler": str(status),
            "score": 0,
            "probleme": "nicht erreichbar",
            "empfehlung": "Neues Design + Hosting prüfen",
            "final_url": final_url or url,
        }

    html_lower = html.lower()
    problems: list[str] = []
    tech: list[str] = []

    uses_https = final_url.startswith("https://") if final_url else url.startswith("https://")
    if not uses_https:
        problems.append("kein HTTPS")

    if not VIEWPORT.search(html):
        problems.append("kein Mobile-Viewport")

    if HTML4.search(html[:2000]):
        problems.append("HTML4/XHTML Doctype")

    if FRAMES.search(html):
        problems.append("Frames/Frameset")

    if FLASH.search(html):
        problems.append("Flash")

    if FONT_TAG.search(html):
        problems.append("<font>-Tags")

    if CENTER_TAG.search(html):
        problems.append("<center>-Tags")

    if MARQUEE.search(html):
        problems.append("<marquee>")

    if BLINK.search(html):
        problems.append("blink-Effekt")

    if TABLE_LAYOUT.search(html[:100_000]):
        problems.append("Tabellen-Layout")

    if FIXED_WIDTH.search(html[:100_000]):
        problems.append("feste Pixel-Breite")

    if IE_ONLY.search(html[:50_000]):
        problems.append("IE-Kompatibilität")

    jq = OLD_JQUERY.search(html)
    if jq:
        problems.append(f"alte jQuery ({jq.group(0)})")

    for gen in OLD_GENERATORS:
        if gen in html_lower:
            tech.append(gen)
    if tech:
        problems.append(f"alter Generator ({', '.join(tech[:2])})")

    if BUILDER_OLD.search(html[:30_000]) and not MEDIA_QUERY.search(html):
        problems.append("Baukasten ohne Media Queries")

    css_links = len(re.findall(r"<link[^>]+stylesheet", html, re.I))
    if not MEDIA_QUERY.search(html) and css_links <= 1 and len(html) > 5000:
        problems.append("keine Media Queries")

    cy = COPYRIGHT_YEAR.findall(html[:50_000])
    if cy:
        years = [int(y) for y in cy if y.isdigit()]
        if years and max(years) < 2018:
            problems.append(f"Copyright bis {max(years)}")

    score = 100
    weights = {
        "kein HTTPS": 20,
        "kein Mobile-Viewport": 25,
        "HTML4/XHTML Doctype": 15,
        "Frames/Frameset": 20,
        "Flash": 20,
        "<font>-Tags": 10,
        "<center>-Tags": 8,
        "<marquee>": 15,
        "blink-Effekt": 10,
        "Tabellen-Layout": 15,
        "feste Pixel-Breite": 10,
        "IE-Kompatibilität": 8,
        "keine Media Queries": 12,
        "Baukasten ohne Media Queries": 10,
    }
    for p in problems:
        for key, w in weights.items():
            if p.startswith(key) or p == key:
                score -= w
                break
        else:
            if p.startswith("alte jQuery"):
                score -= 10
            elif p.startswith("Copyright"):
                score -= 12
            elif p.startswith("alter Generator"):
                score -= 10

    score = max(0, min(100, score))

    if score >= 75:
        empfehlung = "OK – ggf. kleine Updates"
    elif score >= 50:
        empfehlung = "Modernisierung empfohlen"
    elif score >= 25:
        empfehlung = "Redesign empfohlen"
    else:
        empfehlung = "Dringend neues Design"

    return {
        "final_url": final_url or url,
        "https": uses_https,
        "viewport": bool(VIEWPORT.search(html)),
        "score": score,
        "probleme": "; ".join(problems) if problems else "keine",
        "empfehlung": empfehlung,
        "status": status,
        "fehler": "",
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "output" / "aerzte_erlangen.csv"
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "output" / "aerzte_erlangen_audit.csv"

    rows = list(csv.DictReader(in_path.open(encoding="utf-8")))
    with_site = [r for r in rows if r.get("website", "").strip()]

    print(f"Prüfe {len(with_site)} Websites …\n")

    results: list[dict] = []
    for i, row in enumerate(with_site, 1):
        url = row["website"].strip()
        print(f"[{i}/{len(with_site)}] {row['name'][:50]} …", flush=True)
        audit = audit_website(url)
        results.append({**row, **audit})
        print(f"  Score: {audit['score']} | {audit['empfehlung']} | {audit.get('probleme', '-')}")

    results.sort(key=lambda r: r.get("score", 0))

    fields = list(rows[0].keys()) + [
        "final_url", "https", "viewport", "score", "probleme", "empfehlung", "status", "fehler",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    redesign = [r for r in results if r.get("score", 100) < 50]
    print(f"\nFertig: {out_path}")
    print(f"  Redesign-Kandidaten (Score < 50): {len(redesign)}")
    print(f"  Modernisierung (50–74): {sum(1 for r in results if 50 <= r.get('score', 0) < 75)}")
    print(f"  OK (≥ 75): {sum(1 for r in results if r.get('score', 0) >= 75)}")

    print("\nTop Redesign-Kandidaten:")
    for r in results[:15]:
        if r.get("score", 100) < 75:
            print(f"  [{r['score']}] {r['name']}")
            print(f"       {r.get('website')} → {r.get('probleme')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
