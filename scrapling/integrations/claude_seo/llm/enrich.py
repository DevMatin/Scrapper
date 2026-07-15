from __future__ import annotations

from typing import Any

from scrapling.integrations.claude_seo.llm.client import chat_json
from scrapling.integrations.claude_seo.llm.prompts import build_system_prompt, build_user_prompt

CONTENT_EXCERPT_LIMIT = 8000


def enrich_scan(
    report: dict[str, Any],
    *,
    lead_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if report.get("error"):
        return {"error": report["error"]}

    system = build_system_prompt()
    user = build_user_prompt(report, lead_meta=lead_meta)
    return chat_json(system, user)
