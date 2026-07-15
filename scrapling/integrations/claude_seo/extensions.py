from __future__ import annotations

import subprocess

from scrapling.integrations.claude_seo.cursor_sync import install_extension, list_extensions


def extension_status(name: str) -> dict:
    try:
        proc = install_extension(name)
        return {
            "name": name,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except FileNotFoundError as exc:
        return {"name": name, "error": str(exc)}


def run_extension_mcp_hint(name: str) -> str:
    hints = {
        "dataforseo": "npx dataforseo-mcp-server (separate MCP process)",
        "firecrawl": "npx firecrawl-mcp (separate MCP process)",
        "banana": "npx @ycse/nanobanana-mcp (separate MCP process)",
        "ahrefs": "npx @ahrefs/mcp (separate MCP process)",
        "unlighthouse": "npx unlighthouse (via scrapling seo run unlighthouse_run)",
    }
    return hints.get(name, f"See claude-seo-main/extensions/{name}/docs/")
