from __future__ import annotations

import json
import sys

try:
    from click import argument, command, group, option
except ImportError as e:
    raise ModuleNotFoundError("scrapling seo requires click (pip install scrapling[fetchers])") from e

from scrapling.integrations.claude_seo.config import ensure_config_layout, get_claude_seo_root
from scrapling.integrations.claude_seo.cursor_sync import list_extensions, sync_cursor_rules
from scrapling.integrations.claude_seo.extensions import extension_status, run_extension_mcp_hint
from scrapling.integrations.claude_seo.orchestrator.audit import run_audit
from scrapling.integrations.claude_seo.orchestrator.lead_batch import scan_leads
from scrapling.integrations.claude_seo.orchestrator.pipeline import run_pipeline
from scrapling.integrations.claude_seo.orchestrator.page_scan import (
    scan_content,
    scan_page,
    scan_schema,
    scan_technical,
    domain_label,
)
from scrapling.integrations.claude_seo.registry import CLI_COMMANDS, capability_ids, get_capability
from scrapling.integrations.claude_seo.runner import run_capability
from scrapling.integrations.claude_seo.llm.enrich import enrich_scan
from scrapling.integrations.claude_seo.supabase_store import fetch_leads_with_websites


def _emit(data: dict, as_json: bool) -> None:
    if as_json:
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        scores = data.get("scores") or {}
        print(f"URL: {data.get('url')}")
        if scores:
            print(f"Health: {scores.get('health')}/100")
        if data.get("issues"):
            print("Issues:")
            for issue in data["issues"]:
                print(f"  [{issue.get('severity')}] {issue.get('title')}")


@group(name="seo", help="Claude SEO integration (vendor: claude-seo-main)")
def seo():
    ensure_config_layout()


@seo.command("page", help=CLI_COMMANDS["page"])
@argument("url")
@option("--json", "as_json", is_flag=True, default=False)
@option("--no-pagespeed", is_flag=True, default=False)
@option("--llm", is_flag=True, default=False, help="OpenAI-Anreicherung (E-E-A-T, Action Plan)")
def seo_page(url: str, as_json: bool, no_pagespeed: bool, llm: bool):
    data = scan_page(url, include_pagespeed=not no_pagespeed)
    if llm and not data.get("error"):
        try:
            data["llm_analysis"] = enrich_scan(data)
        except Exception as exc:
            data["llm_analysis"] = {"error": str(exc)}
    _emit(data, as_json)


@seo.command("content", help=CLI_COMMANDS["content"])
@argument("url")
@option("--json", "as_json", is_flag=True, default=False)
def seo_content(url: str, as_json: bool):
    data = scan_content(url)
    _emit(data, as_json)


@seo.command("technical", help=CLI_COMMANDS["technical"])
@argument("url")
@option("--json", "as_json", is_flag=True, default=False)
def seo_technical(url: str, as_json: bool):
    data = scan_technical(url)
    _emit(data, as_json)


@seo.command("schema", help=CLI_COMMANDS["schema"])
@argument("url")
@option("--json", "as_json", is_flag=True, default=False)
def seo_schema_cmd(url: str, as_json: bool):
    data = scan_schema(url)
    _emit(data, as_json)


@seo.command("audit", help=CLI_COMMANDS["audit"])
@argument("url")
@option("--output", "-o", default=None, help="Output directory")
@option("--max-pages", default=50, show_default=True)
@option("--json", "as_json", is_flag=True, default=False)
def seo_audit(url: str, output: str | None, max_pages: int, as_json: bool):
    out = output or f"{domain_label(url)}-audit"
    data = run_audit(url, out, max_pages=max_pages)
    if as_json:
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print(f"Audit written to {out}")
        print(f"Health: {(data.get('summary') or {}).get('health_score')}/100")


@seo.command("run", help=CLI_COMMANDS["run"])
@argument("script_id")
@option("--url", default=None)
@option("--json", "as_json", is_flag=True, default=False)
def seo_run(script_id: str, url: str | None, as_json: bool):
    cap = get_capability(script_id)
    data = run_capability(cap.id, url=url)
    if as_json:
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False, default=str)
        sys.stdout.write("\n")
    else:
        print(data)


@seo.command("list", help="List registered SEO scripts")
@option("--json", "as_json", is_flag=True, default=False)
def seo_list(as_json: bool):
    if as_json:
        json.dump({"scripts": capability_ids()}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for sid in capability_ids():
            print(sid)


@seo.command("leads-scan", help="Scan leads with websites from Supabase")
@option("--limit", default=20, show_default=True)
@option("--json", "as_json", is_flag=True, default=False)
@option("--llm", is_flag=True, default=False, help="OpenAI-Anreicherung")
def seo_leads_scan(limit: int, as_json: bool, llm: bool):
    leads = fetch_leads_with_websites(limit=limit)
    results = scan_leads(leads, persist=True, llm=llm)
    if as_json:
        json.dump(results, sys.stdout, indent=2, ensure_ascii=False, default=str)
        sys.stdout.write("\n")
    else:
        print(f"Scanned {len(results)} leads")


@seo.command("pipeline", help="Google Places → Leads mit Website → SEO-Scan → OpenAI")
@argument("query")
@option("--limit", default=10, show_default=True)
@option("--no-llm", is_flag=True, default=False)
@option("--no-persist", is_flag=True, default=False)
@option("--json", "as_json", is_flag=True, default=False)
def seo_pipeline(query: str, limit: int, no_llm: bool, no_persist: bool, as_json: bool):
    results = run_pipeline(
        query,
        limit=limit,
        llm=not no_llm,
        persist=not no_persist,
    )
    if as_json:
        json.dump(results, sys.stdout, indent=2, ensure_ascii=False, default=str)
        sys.stdout.write("\n")
    else:
        print(f"Pipeline abgeschlossen: {len(results)} Leads")
        for entry in results:
            health = (entry.get("report") or {}).get("scores", {}).get("health")
            print(f"  - {entry.get('name')} | Health: {health}/100 | {entry.get('url')}")


@seo.command("install-cursor", help=CLI_COMMANDS["install-cursor"])
@option("--force", is_flag=True, default=False)
def seo_install_cursor(force: bool):
    paths = sync_cursor_rules(force=force)
    print(f"Linked {len(paths)} Cursor rule files")
    print(f"Vendor root: {get_claude_seo_root()}")


@seo.group("ext", help=CLI_COMMANDS["ext"])
def seo_ext():
    pass


@seo_ext.command("list")
def seo_ext_list():
    for name in list_extensions():
        print(name)


@seo_ext.command("install")
@argument("name")
def seo_ext_install(name: str):
    result = extension_status(name)
    if result.get("error"):
        print(result["error"], file=sys.stderr)
        sys.exit(1)
    print(result.get("stdout") or run_extension_mcp_hint(name))


@seo.group("drift", help=CLI_COMMANDS["drift"])
def seo_drift():
    pass


@seo_drift.command("baseline")
@argument("url")
@option("--json", "as_json", is_flag=True, default=False)
def seo_drift_baseline(url: str, as_json: bool):
    data = run_capability("drift_baseline", url=url)
    _emit({"url": url, "result": data}, as_json)


@seo_drift.command("compare")
@argument("url")
@option("--json", "as_json", is_flag=True, default=False)
def seo_drift_compare(url: str, as_json: bool):
    data = run_capability("drift_compare", url=url)
    _emit({"url": url, "result": data}, as_json)


@seo.group("google", help=CLI_COMMANDS["google"])
def seo_google():
    pass


@seo_google.command("pagespeed")
@argument("url")
@option("--json", "as_json", is_flag=True, default=False)
def seo_google_pagespeed(url: str, as_json: bool):
    data = run_capability("pagespeed_check", url=url)
    _emit({"url": url, "result": data}, as_json)
