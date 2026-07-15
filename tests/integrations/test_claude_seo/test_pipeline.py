from __future__ import annotations

from unittest.mock import patch

import pytest

MOCK_LEADS = [
    {
        "id": "lead-1",
        "name": "Test Café",
        "website": "https://example.com/",
        "branche": "cafe",
        "ort": "Erlangen",
    }
]

MOCK_REPORT = {
    "url": "https://example.com/",
    "scores": {"health": 80, "on_page": 85, "content": 75, "technical": 90, "schema": 70, "images": 80},
    "issues": [],
    "content_excerpt": "Test content",
}

MOCK_LLM = {
    "business_type": "local",
    "summary": {"narrative": "OK", "top_findings": [], "quick_wins": []},
    "eeat": {"experience": 70, "expertise": 70, "authoritativeness": 70, "trustworthiness": 70},
    "categories": [],
    "action_plan": {"phases": []},
    "model": "gpt-4.1-mini",
    "generated_at": "2026-07-15T10:00:00+00:00",
}


def test_run_pipeline_mock():
    with patch(
        "scrapling.integrations.claude_seo.orchestrator.pipeline.fetch_and_save_leads",
        return_value=MOCK_LEADS,
    ):
        with patch(
            "scrapling.integrations.claude_seo.orchestrator.pipeline.fetch_leads_for_query",
            return_value=MOCK_LEADS,
        ):
            with patch(
                "scrapling.integrations.claude_seo.orchestrator.pipeline.resolve_lead_ids",
                return_value=MOCK_LEADS,
            ):
                with patch(
                    "scrapling.integrations.claude_seo.orchestrator.page_scan.scan_page",
                    return_value=MOCK_REPORT,
                ):
                    with patch(
                        "scrapling.integrations.claude_seo.orchestrator.pipeline.enrich_scan",
                        return_value=MOCK_LLM,
                    ):
                        with patch(
                            "scrapling.integrations.claude_seo.orchestrator.pipeline.save_audit",
                            return_value="audit-1",
                        ):
                            from scrapling.integrations.claude_seo.orchestrator.pipeline import run_pipeline

                            results = run_pipeline("Café in Erlangen", limit=1, llm=True, persist=True)
                            assert len(results) == 1
                            assert results[0]["llm_analysis"]["business_type"] == "local"
                            assert results[0]["audit_id"] == "audit-1"


def test_filter_places_with_website():
    from scrapling.integrations.claude_seo.places import filter_places

    places = [
        {"websiteUri": "https://a.de"},
        {"websiteUri": None},
    ]
    assert len(filter_places(places, "with")) == 1
    assert len(filter_places(places, "without")) == 1
    assert len(filter_places(places, "all")) == 2


def test_place_to_lead():
    from scrapling.integrations.claude_seo.places import place_to_lead

    lead = place_to_lead(
        {
            "displayName": {"text": "Café Test"},
            "formattedAddress": "Hauptstr. 1, 91054 Erlangen, Germany",
            "nationalPhoneNumber": "+491234",
            "websiteUri": "https://cafe.test",
            "types": ["cafe", "point_of_interest"],
        }
    )
    assert lead["name"] == "Café Test"
    assert lead["hat_website"] is True
    assert lead["ort"] == "91054 Erlangen"
