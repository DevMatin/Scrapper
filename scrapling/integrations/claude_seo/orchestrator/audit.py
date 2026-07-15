from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from scrapling.integrations.claude_seo.fetch_adapter import fetch_page
from scrapling.integrations.claude_seo.orchestrator.page_scan import domain_label, scan_page
from scrapling.integrations.claude_seo.runner import call_module_function, patched_seo_environment


def _same_domain(base: str, candidate: str) -> bool:
    return urlparse(base).netloc == urlparse(candidate).netloc


def crawl_urls(start_url: str, max_pages: int = 500) -> list[str]:
    seen: set[str] = set()
    queue: deque[str] = deque([start_url])
    result: list[str] = []

    while queue and len(result) < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        fetched = fetch_page(url)
        if fetched.get("error") or not fetched.get("content"):
            continue
        result.append(fetched.get("url") or url)
        with patched_seo_environment():
            parsed = call_module_function("parse_html", "parse_html", fetched["content"], fetched.get("url") or url)
        for link in (parsed.get("links") or {}).get("internal") or []:
            href = link.get("href")
            if not href or href in seen:
                continue
            if _same_domain(start_url, href):
                queue.append(href.split("#")[0])
    return result


def run_audit(url: str, output_dir: str | Path, *, max_pages: int = 50) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    findings_dir = out / "findings"
    findings_dir.mkdir(exist_ok=True)

    pages = crawl_urls(url, max_pages=max_pages)
    if url not in pages:
        pages.insert(0, url)

    page_reports: list[dict] = []
    for page_url in pages:
        try:
            page_reports.append(scan_page(page_url, include_pagespeed=False))
        except Exception as exc:
            page_reports.append({"url": page_url, "error": str(exc)})

    homepage = page_reports[0] if page_reports else scan_page(url)
    scores = homepage.get("scores") or {}
    health = int(scores.get("health") or 0)

    categories = [
        {
            "name": "On-Page SEO",
            "score": scores.get("on_page", 0),
            "findings": [i for i in homepage.get("issues", []) if i.get("severity") in ("critical", "high")],
        },
        {
            "name": "Content Quality",
            "score": scores.get("content", 0),
            "findings": [],
        },
        {
            "name": "Technical SEO",
            "score": scores.get("technical", 0),
            "findings": [],
        },
        {
            "name": "Schema",
            "score": scores.get("schema", 0),
            "findings": [],
        },
        {
            "name": "Images",
            "score": scores.get("images", 0),
            "findings": [],
        },
    ]

    audit_data = {
        "summary": {
            "health_score": health,
            "pages_crawled": len(page_reports),
            "top_findings": homepage.get("issues", [])[:10],
        },
        "categories": categories,
        "pages": page_reports,
        "artifacts": {"findings_dir": "findings/", "output_dir": str(out)},
    }

    (out / "audit-data.json").write_text(json.dumps(audit_data, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "FULL-AUDIT-REPORT.md").write_text(_markdown_report(audit_data), encoding="utf-8")
    (findings_dir / "content.md").write_text(_findings_md("Content", homepage), encoding="utf-8")
    (findings_dir / "technical.md").write_text(_findings_md("Technical", homepage), encoding="utf-8")

    return audit_data


def _findings_md(title: str, report: dict) -> str:
    lines = [f"# {title} Findings", "", f"URL: {report.get('url')}", ""]
    for issue in report.get("issues") or []:
        lines.append(f"- **{issue.get('severity')}**: {issue.get('title')}")
    return "\n".join(lines) + "\n"


def _markdown_report(data: dict) -> str:
    summary = data.get("summary") or {}
    lines = [
        f"# SEO Audit Report",
        "",
        f"Health Score: **{summary.get('health_score', 0)}/100**",
        f"Pages crawled: {summary.get('pages_crawled', 0)}",
        "",
        "## Top Findings",
    ]
    for item in summary.get("top_findings") or []:
        lines.append(f"- [{item.get('severity')}] {item.get('title')}")
    return "\n".join(lines) + "\n"
