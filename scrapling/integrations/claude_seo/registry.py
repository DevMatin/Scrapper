from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class SeoCapability:
    id: str
    script: str
    category: str
    requires_url: bool = False
    requires_api: tuple[str, ...] = ()
    cli_command: str | None = None
    mcp_tool: str | None = None
    description: str = ""


def _cap(
    id: str,
    category: str,
    *,
    requires_url: bool = False,
    requires_api: tuple[str, ...] = (),
    cli_command: str | None = None,
    mcp_tool: str | None = None,
    description: str = "",
) -> SeoCapability:
    return SeoCapability(
        id=id,
        script=f"{id}.py",
        category=category,
        requires_url=requires_url,
        requires_api=requires_api,
        cli_command=cli_command,
        mcp_tool=mcp_tool,
        description=description,
    )


CAPABILITIES: tuple[SeoCapability, ...] = (
    _cap("parse_html", "page", description="Parse HTML for SEO elements"),
    _cap("content_quality", "content", mcp_tool="seo_content_score", description="QRG content quality scorer"),
    _cap("content_verify", "content", description="Claim and citation gap detector"),
    _cap("content_humanize", "content", description="AI-pattern phrase replacer"),
    _cap("preload_check", "technical", requires_url=True, description="Speculation/bfcache/preload audit"),
    _cap("schema_generate", "schema", mcp_tool="seo_schema", description="JSON-LD generators"),
    _cap("schema_ecommerce_validate", "schema", description="Product schema validator"),
    _cap("iptc_ai_label", "images", description="IPTC DigitalSourceType audit"),
    _cap("portability_check", "utility", description="SKILL.md portability lint"),
    _cap("render_page", "page", requires_url=True, description="Headless page render (via Scrapling adapter)"),
    _cap("fetch_page", "page", requires_url=True, description="Raw page fetch (via Scrapling adapter)"),
    _cap("agent_ux_check", "technical", requires_url=True, cli_command="technical", description="Agent-friendly page audit"),
    _cap("analyze_visual", "visual", requires_url=True, description="Visual analysis via Playwright"),
    _cap("capture_screenshot", "visual", requires_url=True, description="Screenshot capture"),
    _cap("domain_history", "technical", requires_url=True, description="WHOIS domain heritage check"),
    _cap("gbp_deprecation_lint", "local", requires_url=True, description="GBP deprecation linter"),
    _cap("nlp_analyze", "google", requires_url=True, requires_api=("google_api_key",), description="Google Cloud NLP"),
    _cap("parasite_risk", "technical", requires_url=True, description="Parasite SEO risk scanner"),
    _cap("ucp_check", "ecommerce", requires_url=True, description="UCP profile auditor"),
    _cap("verify_backlinks", "backlinks", requires_url=True, description="Verify backlinks exist"),
    _cap("pagespeed_check", "google", requires_url=True, requires_api=("google_api_key",), cli_command="google pagespeed", mcp_tool="seo_pagespeed", description="PageSpeed + CrUX"),
    _cap("crux_history", "google", requires_url=True, requires_api=("google_api_key",), description="CrUX history trends"),
    _cap("lcp_subparts", "google", requires_url=True, requires_api=("google_api_key",), description="LCP subparts via CrUX"),
    _cap("gsc_query", "google", requires_api=("google_oauth",), cli_command="google gsc", description="Search Console queries"),
    _cap("gsc_inspect", "google", requires_url=True, requires_api=("google_oauth",), description="URL Inspection API"),
    _cap("ga4_report", "google", requires_api=("google_oauth",), description="GA4 organic reports"),
    _cap("indexing_notify", "google", requires_url=True, requires_api=("google_oauth",), description="Indexing API notify"),
    _cap("keyword_planner", "google", requires_api=("google_ads",), description="Keyword Planner"),
    _cap("google_report", "google", cli_command="google report", description="PDF/HTML report generator"),
    _cap("google_auth", "google", description="Google credential manager"),
    _cap("youtube_search", "google", requires_api=("google_api_key",), description="YouTube Data API search"),
    _cap("moz_api", "backlinks", requires_api=("moz",), description="Moz Link Explorer"),
    _cap("bing_webmaster", "backlinks", requires_api=("bing",), description="Bing Webmaster Tools"),
    _cap("commoncrawl_graph", "backlinks", description="Common Crawl web graph"),
    _cap("validate_backlink_report", "backlinks", description="Backlink report validator"),
    _cap("backlinks_auth", "backlinks", description="Backlink API credential manager"),
    _cap("dataforseo_merchant", "dataforseo", requires_api=("dataforseo",), description="DataForSEO merchant data"),
    _cap("dataforseo_normalize", "dataforseo", description="DataForSEO response normalizer"),
    _cap("dataforseo_costs", "dataforseo", description="DataForSEO cost tracking"),
    _cap("drift_baseline", "drift", requires_url=True, cli_command="drift baseline", description="SEO drift baseline"),
    _cap("drift_compare", "drift", requires_url=True, cli_command="drift compare", description="Compare to baseline"),
    _cap("drift_history", "drift", requires_url=True, cli_command="drift history", description="Drift history query"),
    _cap("drift_report", "drift", cli_command="drift report", description="Drift HTML report"),
    _cap("seo_updates", "utility", description="Google updates changelog query"),
    _cap("sync_flow", "utility", description="FLOW prompt library sync"),
    _cap("release_sign", "utility", description="Release manifest signer"),
    _cap("verify_release", "utility", description="Release integrity verifier"),
    _cap("indexnow_submit", "technical", requires_url=True, description="IndexNow submitter"),
    _cap("unlighthouse_run", "technical", requires_url=True, description="Unlighthouse CLI wrapper"),
    _cap("url_safety", "utility", description="URL/SSRF safety helpers"),
)

SKILLS: tuple[str, ...] = (
    "seo",
    "seo-audit",
    "seo-page",
    "seo-technical",
    "seo-content",
    "seo-content-brief",
    "seo-schema",
    "seo-geo",
    "seo-images",
    "seo-sitemap",
    "seo-plan",
    "seo-competitor-pages",
    "seo-programmatic",
    "seo-local",
    "seo-maps",
    "seo-hreflang",
    "seo-google",
    "seo-backlinks",
    "seo-cluster",
    "seo-sxo",
    "seo-drift",
    "seo-ecommerce",
    "seo-flow",
    "seo-dataforseo",
    "seo-image-gen",
)

AGENTS: tuple[str, ...] = (
    "seo-backlinks",
    "seo-cluster",
    "seo-content",
    "seo-dataforseo",
    "seo-drift",
    "seo-ecommerce",
    "seo-flow",
    "seo-geo",
    "seo-google",
    "seo-image-gen",
    "seo-local",
    "seo-maps",
    "seo-performance",
    "seo-schema",
    "seo-sitemap",
    "seo-sxo",
    "seo-technical",
    "seo-visual",
)

EXTENSIONS: tuple[str, ...] = (
    "dataforseo",
    "firecrawl",
    "banana",
    "ahrefs",
    "seranking",
    "profound",
    "bing-webmaster",
    "unlighthouse",
)

CLI_COMMANDS: dict[str, str] = {
    "page": "Full single-page SEO scan",
    "audit": "Multi-page site audit",
    "content": "E-E-A-T and content quality",
    "technical": "Technical SEO audit",
    "schema": "Schema.org detection and validation",
    "geo": "Generative Engine Optimization",
    "local": "Local SEO analysis",
    "images": "Image SEO audit",
    "sitemap": "Sitemap analysis",
    "backlinks": "Backlink profile",
    "drift": "SEO drift monitoring",
    "ecommerce": "E-commerce SEO",
    "google": "Google API tools",
    "run": "Run any registered script by id",
    "install-cursor": "Symlink skills/agents into .cursor/rules/",
    "ext": "Manage optional extensions",
}


def iter_capabilities() -> Iterator[SeoCapability]:
    yield from CAPABILITIES


def get_capability(script_id: str) -> SeoCapability:
    for cap in CAPABILITIES:
        if cap.id == script_id:
            return cap
    raise KeyError(f"Unknown SEO capability: {script_id}")


def capability_ids() -> list[str]:
    return [c.id for c in CAPABILITIES]
