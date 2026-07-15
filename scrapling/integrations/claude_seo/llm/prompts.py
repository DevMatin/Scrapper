from __future__ import annotations

import re
from functools import lru_cache

from scrapling.integrations.claude_seo.config import get_agents_dir, get_claude_seo_root

_AGENT_FILES = ("seo-content.md", "seo-technical.md", "seo-geo.md")
_FRAMEWORK = "skills/seo/references/thinking-framework.md"


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        match = re.match(r"---\n.*?\n---\n", text, re.DOTALL)
        if match:
            return text[match.end() :].strip()
    return text.strip()


@lru_cache(maxsize=1)
def load_agent_prompts() -> str:
    parts: list[str] = []
    agents_dir = get_agents_dir()
    for name in _AGENT_FILES:
        path = agents_dir / name
        if path.is_file():
            parts.append(f"## {name}\n\n{_strip_frontmatter(path.read_text(encoding='utf-8'))}")

    root = get_claude_seo_root()
    framework_path = root / _FRAMEWORK
    if framework_path.is_file():
        parts.append(f"## Synthesis Framework\n\n{framework_path.read_text(encoding='utf-8')}")

    return "\n\n---\n\n".join(parts)


def build_system_prompt() -> str:
    return (
        "Du bist ein SEO-Audit-Spezialist. Analysiere die bereitgestellten Script-Ergebnisse "
        "und den Seiteninhalt. Die deterministischen Scores und Issues aus dem Script-Scan "
        "sind die primäre Evidenz — interpretiere sie, ergänze E-E-A-T-Bewertung und erstelle "
        "priorisierte Empfehlungen.\n\n"
        "Antworte ausschließlich als valides JSON gemäß dem vorgegebenen Schema.\n\n"
        + load_agent_prompts()
    )


def build_user_prompt(
    report: dict,
    *,
    lead_meta: dict | None = None,
) -> str:
    compact = {
        "url": report.get("url"),
        "scores": report.get("scores"),
        "issues": report.get("issues"),
        "on_page_seo": report.get("on_page_seo"),
        "schema": report.get("schema"),
        "content_quality": report.get("content_quality"),
        "content_verify": report.get("content_verify"),
        "preload": report.get("preload"),
        "images": report.get("images"),
    }
    import json

    parts = [
        "Analysiere diesen SEO-Scan und erstelle eine LLM-Anreicherung.",
        f"\nScript-Scan:\n```json\n{json.dumps(compact, ensure_ascii=False, indent=2)}\n```",
    ]
    excerpt = report.get("content_excerpt")
    if excerpt:
        parts.append(f"\nSeiteninhalt (Auszug):\n```\n{excerpt}\n```")
    if lead_meta:
        parts.append(f"\nLead-Kontext:\n```json\n{json.dumps(lead_meta, ensure_ascii=False)}\n```")
    parts.append(
        "\nErkenne business_type (local|saas|ecommerce|publisher|agency). "
        "Bewerte E-E-A-T (0-100 pro Faktor). "
        "Erstelle categories mit findings (severity: Critical|High|Medium|Low|Info) "
        "und action_plan mit 4 Phasen."
    )
    return "\n".join(parts)
