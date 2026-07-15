from __future__ import annotations

from unittest.mock import patch

MOCK_LLM_RESPONSE = {
    "business_type": "local",
    "summary": {
        "narrative": "Lokales Café mit solider Basis, aber Content-Lücken.",
        "top_findings": ["Fehlende Meta-Description"],
        "quick_wins": ["Alt-Texte ergänzen"],
    },
    "eeat": {
        "experience": 70,
        "expertise": 65,
        "authoritativeness": 60,
        "trustworthiness": 75,
    },
    "categories": [
        {
            "name": "Content Quality",
            "score": 72,
            "findings": [
                {
                    "title": "Dünner Content",
                    "severity": "Medium",
                    "description": "Wenig Text auf der Startseite.",
                    "recommendation": "Mehr lokalen Content ergänzen.",
                }
            ],
        }
    ],
    "action_plan": {
        "phases": [
            {
                "name": "Phase 1: Critical Fixes",
                "timeframe": "Week 1",
                "items": ["Meta-Description hinzufügen"],
            }
        ]
    },
    "model": "gpt-4.1-mini",
    "generated_at": "2026-07-15T10:00:00+00:00",
}

MOCK_REPORT = {
    "url": "https://example.com/",
    "scores": {"health": 78, "on_page": 80, "content": 70, "technical": 85, "schema": 60, "images": 75},
    "issues": [{"severity": "high", "title": "Fehlende Meta-Description"}],
    "on_page_seo": {"title": "Test Café", "word_count": 400},
    "content_excerpt": "Willkommen in unserem Café in Erlangen.",
}


def test_enrich_scan_calls_openai():
    with patch(
        "scrapling.integrations.claude_seo.llm.enrich.chat_json",
        return_value=MOCK_LLM_RESPONSE,
    ):
        from scrapling.integrations.claude_seo.llm.enrich import enrich_scan

        result = enrich_scan(MOCK_REPORT)
        assert result["business_type"] == "local"
        assert result["eeat"]["trustworthiness"] == 75


def test_enrich_scan_error_report():
    from scrapling.integrations.claude_seo.llm.enrich import enrich_scan

    result = enrich_scan({"url": "https://x.com", "error": "timeout"})
    assert result["error"] == "timeout"


def test_load_agent_prompts():
    from scrapling.integrations.claude_seo.llm.prompts import load_agent_prompts

    text = load_agent_prompts()
    assert "E-E-A-T" in text or "Content Quality" in text


def test_azure_config_preferred(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_BASE_URL", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from scrapling.integrations.claude_seo.llm.client import get_azure_openai_config, get_llm_model

    cfg = get_azure_openai_config()
    assert cfg is not None
    assert cfg["deployment"] == "gpt-test"
    assert get_llm_model() == "gpt-test"


def test_create_chat_client_uses_azure(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_BASE_URL", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-test")

    mock_azure_cls = patch("openai.AzureOpenAI")
    with mock_azure_cls as azure_cls:
        from scrapling.integrations.claude_seo.llm.client import _create_chat_client

        _create_chat_client()
        azure_cls.assert_called_once_with(
            azure_endpoint="https://test.openai.azure.com",
            api_key="azure-key",
            api_version="2024-12-01-preview",
        )
