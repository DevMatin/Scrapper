from __future__ import annotations

from typing import Any

from scrapling.integrations.claude_seo.orchestrator.lead_batch import scan_leads
from scrapling.integrations.claude_seo.orchestrator.page_scan import scan_content, scan_page, scan_schema
from scrapling.integrations.claude_seo.orchestrator.pipeline import run_pipeline
from scrapling.integrations.claude_seo.llm.enrich import enrich_scan
from scrapling.integrations.claude_seo.runner import patched_seo_environment, call_module_function
from scrapling.integrations.claude_seo.fetch_adapter import render_page
from scrapling.integrations.claude_seo.config import get_google_api_key


def seo_page_scan(url: str, include_pagespeed: bool = True) -> dict[str, Any]:
    return scan_page(url, include_pagespeed=include_pagespeed)


def seo_content_score(url: str) -> dict[str, Any]:
    return scan_content(url)


def seo_parse(url: str) -> dict[str, Any]:
    render = render_page(url, mode="auto")
    html = render.get("content") or ""
    with patched_seo_environment():
        parsed = call_module_function("parse_html", "parse_html", html, url)
    return {"url": render.get("url"), "parsed": parsed}


def seo_schema(url: str) -> dict[str, Any]:
    return scan_schema(url)


def seo_pagespeed(url: str) -> dict[str, Any]:
    if not get_google_api_key():
        return {"error": "GOOGLE_API_KEY or GOOGLE_MAPS_API_KEY not configured"}
    with patched_seo_environment():
        return call_module_function(
            "pagespeed_check",
            "combined_check",
            url,
            api_key=get_google_api_key(),
        )


def seo_audit(url: str, output_dir: str = "./audit", max_pages: int = 50) -> dict[str, Any]:
    from scrapling.integrations.claude_seo.orchestrator.audit import run_audit

    return run_audit(url, output_dir, max_pages=max_pages)


def seo_leads_scan(limit: int = 20, llm: bool = False) -> list[dict[str, Any]]:
    from scrapling.integrations.claude_seo.supabase_store import fetch_leads_with_websites

    leads = fetch_leads_with_websites(limit=limit)
    return scan_leads(leads, persist=True, llm=llm)


def seo_llm_enrich(url: str) -> dict[str, Any]:
    report = scan_page(url, include_pagespeed=False)
    if report.get("error"):
        return report
    try:
        return enrich_scan(report)
    except Exception as exc:
        return {"error": str(exc), "url": url}


def seo_pipeline(query: str, limit: int = 10, llm: bool = True) -> list[dict[str, Any]]:
    return run_pipeline(query, limit=limit, llm=llm, persist=True)
