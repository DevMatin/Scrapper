from __future__ import annotations

from typing import Any, Iterable

from scrapling.integrations.claude_seo.llm.enrich import enrich_scan
from scrapling.integrations.claude_seo.orchestrator.page_scan import scan_page
from scrapling.integrations.claude_seo.supabase_store import save_audit


def scan_leads(
    leads: Iterable[dict[str, Any]],
    *,
    persist: bool = True,
    include_pagespeed: bool = False,
    llm: bool = False,
) -> list[dict[str, Any]]:
    results: list[dict] = []
    for lead in leads:
        website = (lead.get("website") or lead.get("websiteUri") or "").strip()
        if not website:
            continue
        if not website.startswith("http"):
            website = f"https://{website}"
        report = scan_page(website, include_pagespeed=include_pagespeed)
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
