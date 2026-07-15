from __future__ import annotations

import os
from typing import Any

from scrapling.integrations.claude_seo.config import load_env
from scrapling.integrations.claude_seo.llm.enrich import enrich_scan
from scrapling.integrations.claude_seo.places import (
    fetch_and_save_leads,
    fetch_leads_for_query,
    resolve_lead_ids,
)
from scrapling.integrations.claude_seo.supabase_store import save_audit


def run_pipeline(
    query: str,
    *,
    limit: int = 10,
    llm: bool = True,
    persist: bool = True,
    skip_duplicates: bool = True,
) -> list[dict[str, Any]]:
    load_env()
    supabase_url = os.environ.get("SUPABASE_URL") or ""
    supabase_key = os.environ.get("SUPABASE_KEY") or ""

    fetch_and_save_leads(
        query,
        limit=limit,
        website_filter="with",
        skip_duplicates=skip_duplicates,
    )

    leads = fetch_leads_for_query(query, limit=limit, website_filter="with")
    if supabase_url and supabase_key:
        leads = resolve_lead_ids(supabase_url, supabase_key, leads)

    results: list[dict[str, Any]] = []
    for lead in leads[:limit]:
        website = (lead.get("website") or "").strip()
        if not website:
            continue
        if not website.startswith("http"):
            website = f"https://{website}"

        from scrapling.integrations.claude_seo.orchestrator.page_scan import scan_page

        report = scan_page(website, include_pagespeed=False)
        llm_analysis = None
        if llm and not report.get("error"):
            try:
                llm_analysis = enrich_scan(
                    report,
                    lead_meta={
                        "name": lead.get("name"),
                        "branche": lead.get("branche"),
                        "ort": lead.get("ort"),
                    },
                )
            except Exception as exc:
                llm_analysis = {"error": str(exc)}

        entry: dict[str, Any] = {
            "lead_id": lead.get("id"),
            "name": lead.get("name"),
            "url": website,
            "report": report,
            "llm_analysis": llm_analysis,
        }
        if persist:
            entry["audit_id"] = save_audit(
                report,
                lead_id=lead.get("id"),
                llm_analysis=llm_analysis,
            )
        results.append(entry)

    return results
