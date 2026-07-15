from __future__ import annotations

from unittest.mock import patch

import pytest

from scrapling.integrations.claude_seo.registry import capability_ids, get_capability
from scrapling.integrations.claude_seo.config import get_claude_seo_root


def test_claude_seo_vendor_present():
    root = get_claude_seo_root()
    assert (root / "scripts" / "parse_html.py").is_file()
    assert (root / "skills" / "seo-page" / "SKILL.md").is_file()


def test_registry_lists_core_scripts():
    ids = capability_ids()
    assert "parse_html" in ids
    assert "content_quality" in ids
    assert "pagespeed_check" in ids
    assert len(ids) >= 45


def test_get_capability():
    cap = get_capability("parse_html")
    assert cap.category == "page"


SAMPLE_HTML = """<!DOCTYPE html>
<html lang="de"><head>
<title>Test Kaffeerösterei Erlangen</title>
<meta name="description" content="Spezialitätenkaffee in Erlangen">
<link rel="canonical" href="https://example.com/">
</head><body>
<h1>Amir der Kaffeemann</h1>
<p>Qualität steht für uns an erster Stelle. Wir rösten Kaffee in Erlangen.</p>
</body></html>"""

MOCK_RENDER = {
    "url": "https://example.com/",
    "status_code": 200,
    "content": SAMPLE_HTML,
    "raw_content": SAMPLE_HTML,
    "is_spa": False,
    "extracted_text": "Amir der Kaffeemann Qualität steht für uns an erster Stelle.",
    "publication_date": None,
    "headers": {},
    "redirect_chain": [],
    "mode_used": "raw",
    "error": None,
}


@pytest.mark.integration
def test_page_scan_offline_mock():
    pytest.importorskip("bs4")
    pytest.importorskip("trafilatura")
    from scrapling.integrations.claude_seo.orchestrator.page_scan import scan_page

    with patch(
        "scrapling.integrations.claude_seo.orchestrator.page_scan.render_page",
        return_value=MOCK_RENDER,
    ):
        report = scan_page("https://example.com/", include_pagespeed=False)

    assert report.get("error") is None
    assert report["on_page_seo"]["title"]
    assert report["scores"]["health"] > 0
    assert report["content_quality"]["overall_quality"] > 0
    assert "content_excerpt" in report
    assert len(report["content_excerpt"]) > 0


@pytest.mark.integration
@pytest.mark.network
def test_page_scan_live_amir():
    pytest.importorskip("bs4")
    from scrapling.integrations.claude_seo.orchestrator.page_scan import scan_page

    report = scan_page("https://amir-kaffeemann.de/", include_pagespeed=False)
    assert report.get("status_code") == 200
    assert report["on_page_seo"]["title"]
    assert report["scores"]["health"] > 0
