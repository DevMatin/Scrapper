from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from scrapling.integrations.claude_seo.config import get_google_api_key
from scrapling.integrations.claude_seo.fetch_adapter import render_page
from scrapling.integrations.claude_seo.llm.enrich import CONTENT_EXCERPT_LIMIT
from scrapling.integrations.claude_seo.runner import call_module_function, patched_seo_environment


def _score_images(parsed: dict) -> tuple[int, list[dict]]:
    images = parsed.get("images") or []
    if not images:
        return 100, []
    missing = sum(1 for img in images if not (img.get("alt") or "").strip())
    score = max(0, 100 - int(missing / max(len(images), 1) * 100))
    issues = []
    if missing:
        issues.append({"severity": "high", "title": f"{missing} Bilder ohne Alt-Text"})
    return score, issues


def _score_on_page(parsed: dict) -> tuple[int, list[dict]]:
    issues: list[dict] = []
    title = parsed.get("title") or ""
    if not title:
        issues.append({"severity": "critical", "title": "Fehlender Title-Tag"})
    h1s = parsed.get("h1") or []
    if not h1s:
        issues.append({"severity": "critical", "title": "Kein H1 gefunden"})
    elif len(h1s) > 1:
        issues.append({"severity": "high", "title": f"Mehrere H1 ({len(h1s)})", "value": h1s})
    if not parsed.get("meta_description"):
        issues.append({"severity": "high", "title": "Fehlende Meta-Description"})
    if not parsed.get("canonical"):
        issues.append({"severity": "medium", "title": "Kein Canonical-Tag"})
    if not parsed.get("open_graph"):
        issues.append({"severity": "medium", "title": "Keine Open-Graph-Tags"})
    penalty = sum({"critical": 25, "high": 15, "medium": 8, "low": 3}.get(i["severity"], 0) for i in issues)
    return max(0, 100 - penalty), issues


def _score_schema(parsed: dict) -> tuple[int, list[dict]]:
    schemas = parsed.get("schema") or []
    if not schemas:
        return 40, [{"severity": "medium", "title": "Kein JSON-LD Schema gefunden"}]
    types = set()
    for item in schemas:
        if isinstance(item, dict):
            t = item.get("@type")
            if isinstance(t, list):
                types.update(str(x) for x in t)
            elif t:
                types.add(str(t))
    score = min(100, 50 + len(types) * 10)
    return score, []


def scan_page(url: str, *, include_pagespeed: bool = True) -> dict[str, Any]:
    render = render_page(url, mode="auto")
    if render.get("error"):
        return {"url": url, "error": render["error"]}

    html = render.get("content") or ""
    extracted = render.get("extracted_text") or ""

    with patched_seo_environment():
        parsed = call_module_function("parse_html", "parse_html", html, url)
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        full_text = soup.get_text(separator="\n", strip=True)
        text_for_quality = extracted or full_text
        quality = call_module_function("content_quality", "analyse", text_for_quality)
        verify = call_module_function("content_verify", "verify", text_for_quality)
        preload_mod = call_module_function("preload_check", "analyse", html, dict(render.get("headers") or {}))
        preload = {"url": render.get("url"), **preload_mod}

    on_page_score, on_page_issues = _score_on_page(parsed)
    content_score = int(quality.get("overall_quality", 0))
    schema_score, schema_issues = _score_schema(parsed)
    images_score, image_issues = _score_images(parsed)
    technical_score = int(preload.get("score", 0))

    issues = on_page_issues + schema_issues + image_issues
    if quality.get("flags"):
        issues.append({"severity": "low", "title": "Content-Flags", "value": quality["flags"]})

    health_score = int(
        (on_page_score * 0.25)
        + (content_score * 0.25)
        + (technical_score * 0.2)
        + (schema_score * 0.15)
        + (images_score * 0.15)
    )

    report: dict[str, Any] = {
        "url": render.get("url"),
        "status_code": render.get("status_code"),
        "mode_used": render.get("mode_used"),
        "is_spa": render.get("is_spa"),
        "publication_date": render.get("publication_date"),
        "scores": {
            "health": health_score,
            "on_page": on_page_score,
            "content": content_score,
            "technical": technical_score,
            "schema": schema_score,
            "images": images_score,
        },
        "on_page_seo": {
            "title": parsed.get("title"),
            "title_length": len(parsed.get("title") or ""),
            "meta_description": parsed.get("meta_description"),
            "meta_description_length": len(parsed.get("meta_description") or ""),
            "meta_robots": parsed.get("meta_robots"),
            "canonical": parsed.get("canonical"),
            "h1": parsed.get("h1"),
            "h2_count": len(parsed.get("h2") or []),
            "h3_count": len(parsed.get("h3") or []),
            "word_count": parsed.get("word_count"),
        },
        "social": {
            "open_graph": parsed.get("open_graph"),
            "twitter_card": parsed.get("twitter_card"),
        },
        "links": parsed.get("links"),
        "images": {
            "total": len(parsed.get("images") or []),
            "missing_alt": sum(1 for i in (parsed.get("images") or []) if not (i.get("alt") or "").strip()),
        },
        "schema": {
            "count": len(parsed.get("schema") or []),
            "types": sorted(
                {
                    str(s.get("@type"))
                    for s in (parsed.get("schema") or [])
                    if isinstance(s, dict) and s.get("@type")
                }
            ),
        },
        "content_quality": quality,
        "content_verify": verify,
        "content_excerpt": (extracted or full_text)[:CONTENT_EXCERPT_LIMIT],
        "preload": preload,
        "issues": sorted(
            issues,
            key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["severity"], 9),
        ),
    }

    if include_pagespeed and get_google_api_key():
        try:
            ps = call_module_function(
                "pagespeed_check",
                "combined_check",
                url,
                api_key=get_google_api_key(),
            )
            report["pagespeed"] = ps
        except Exception as exc:
            report["pagespeed"] = {"error": str(exc)}

    return report


def scan_content(url: str) -> dict[str, Any]:
    report = scan_page(url, include_pagespeed=False)
    return {
        "url": report.get("url"),
        "content_quality": report.get("content_quality"),
        "content_verify": report.get("content_verify"),
        "word_count": (report.get("on_page_seo") or {}).get("word_count"),
        "issues": [i for i in report.get("issues", []) if "Content" in i.get("title", "") or i.get("severity") != "low"],
    }


def scan_technical(url: str) -> dict[str, Any]:
    report = scan_page(url, include_pagespeed=True)
    return {
        "url": report.get("url"),
        "preload": report.get("preload"),
        "pagespeed": report.get("pagespeed"),
        "scores": {"technical": (report.get("scores") or {}).get("technical")},
        "issues": report.get("issues"),
    }


def scan_schema(url: str) -> dict[str, Any]:
    render = render_page(url, mode="auto")
    html = render.get("content") or ""
    with patched_seo_environment():
        parsed = call_module_function("parse_html", "parse_html", html, url)
    return {"url": render.get("url"), "schema": parsed.get("schema"), "schema_meta": report_schema_summary(parsed)}


def report_schema_summary(parsed: dict) -> dict:
    return {
        "count": len(parsed.get("schema") or []),
        "types": [
            s.get("@type") for s in (parsed.get("schema") or []) if isinstance(s, dict)
        ],
    }


def domain_label(url: str) -> str:
    return urlparse(url).netloc.replace(":", "_") or "site"
