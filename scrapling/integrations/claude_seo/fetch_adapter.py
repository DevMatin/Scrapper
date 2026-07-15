from __future__ import annotations

import re
import time
from typing import Any, Literal, Optional

from scrapling.integrations.claude_seo.config import get_scripts_dir

Mode = Literal["auto", "always", "never"]

_SPA_SHELL_PATTERNS = (
    '<div id="root"></div>',
    '<div id="__next">',
    '<div id="app"></div>',
    '<div id="__nuxt">',
    "data-svelte-h=",
    "<astro-island ",
    "you need to enable javascript",
    "please enable javascript",
)
_TAG_STRIP = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")


def _is_spa(raw_html: Optional[str]) -> bool:
    if not raw_html:
        return True
    lc = raw_html.lower()
    if any(pattern in lc for pattern in _SPA_SHELL_PATTERNS):
        return True
    body_start = lc.find("<body")
    body_end = lc.rfind("</body>")
    if body_start != -1 and body_end > body_start:
        body = lc[body_start:body_end]
        text = _WHITESPACE.sub(" ", _TAG_STRIP.sub("", body)).strip()
        if len(text) < 100:
            return True
    return False


def _extract_post_process(html: str, url: str) -> tuple[str | None, str | None]:
    extracted_text: str | None = None
    publication_date: str | None = None
    try:
        import trafilatura

        extracted_text = trafilatura.extract(html, url=url, include_comments=False)
    except Exception:
        pass
    try:
        import htmldate

        publication_date = htmldate.find_date(html, url=url)
    except Exception:
        pass
    return extracted_text, publication_date


def _validate_url(url: str) -> tuple[str, str | None]:
    import sys

    scripts = str(get_scripts_dir())
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        from url_safety import URLSafetyError, validate_url_strict

        return validate_url_strict(url)
    except Exception:
        if "://" not in url:
            url = f"https://{url}"
        return url, None


def _response_html(response: Any) -> str:
    if hasattr(response, "html_content"):
        return str(response.html_content)
    if hasattr(response, "body"):
        body = response.body
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        return str(body)
    return str(response)


def fetch_page(
    url: str,
    timeout: int = 30,
    follow_redirects: bool = True,
    max_redirects: int = 5,
    user_agent: Optional[str] = None,
) -> dict:
    del max_redirects
    result: dict = {
        "url": url,
        "status_code": None,
        "content": None,
        "headers": {},
        "redirect_chain": [],
        "redirect_details": [],
        "error": None,
    }
    try:
        norm_url, _ = _validate_url(url)
    except Exception as exc:
        result["error"] = f"url_safety: {exc}"
        return result

    try:
        from scrapling.fetchers import Fetcher

        kwargs: dict[str, Any] = {"timeout": timeout}
        if user_agent:
            kwargs["headers"] = {"User-Agent": user_agent}
        if not follow_redirects:
            kwargs["follow_redirects"] = False
        response = Fetcher.get(norm_url, **kwargs)
        html = _response_html(response)
        result["url"] = getattr(response, "url", norm_url) or norm_url
        result["status_code"] = int(getattr(response, "status", 0) or 0)
        result["content"] = html
        result["headers"] = dict(getattr(response, "headers", {}) or {})
        history = getattr(response, "history", None) or []
        if history:
            result["redirect_chain"] = [getattr(h, "url", str(h)) for h in history]
            result["redirect_details"] = [
                {"url": getattr(h, "url", str(h)), "status_code": getattr(h, "status", None)}
                for h in history
            ]
    except Exception as exc:
        result["error"] = str(exc)
    return result


def render_page(
    url: str,
    *,
    mode: Mode = "auto",
    viewport: str = "desktop",
    timeout_ms: int = 15000,
    block_resources: Optional[list[str]] = None,
    extract_content: bool = True,
    extract_accessibility: bool = False,
    user_agent: Optional[str] = None,
) -> dict:
    del viewport, block_resources, extract_accessibility
    result: dict = {
        "url": url,
        "status_code": None,
        "content": None,
        "raw_content": None,
        "is_spa": None,
        "extracted_text": None,
        "publication_date": None,
        "accessibility_tree": None,
        "headers": {},
        "redirect_chain": [],
        "console_errors": [],
        "render_engine": None,
        "render_ms": None,
        "mode_used": None,
        "error": None,
    }
    if mode not in ("auto", "always", "never"):
        result["error"] = f"Invalid mode: {mode!r}"
        return result

    try:
        norm_url, _ = _validate_url(url)
        result["url"] = norm_url
    except Exception as exc:
        result["error"] = f"url_safety: {exc}"
        return result

    raw = fetch_page(norm_url, timeout=max(30, timeout_ms // 1000), user_agent=user_agent)
    if raw.get("error"):
        result["error"] = raw["error"]
        return result

    result["raw_content"] = raw.get("content")
    result["redirect_chain"] = [
        {"url": u, "status_code": None} if isinstance(u, str) else u
        for u in raw.get("redirect_details") or []
    ] or [{"url": u, "status_code": None} for u in raw.get("redirect_chain") or []]
    result["is_spa"] = _is_spa(result["raw_content"])
    should_render = mode == "always" or (mode == "auto" and result["is_spa"])

    if not should_render:
        result["mode_used"] = "raw"
        result["url"] = raw.get("url") or norm_url
        result["status_code"] = raw.get("status_code")
        result["headers"] = raw.get("headers") or {}
        result["content"] = result["raw_content"]
    else:
        started = time.perf_counter()
        try:
            from scrapling.fetchers import DynamicFetcher

            kwargs: dict[str, Any] = {"timeout": timeout_ms, "network_idle": True}
            if user_agent:
                kwargs["headers"] = {"User-Agent": user_agent}
            response = DynamicFetcher.fetch(norm_url, **kwargs)
            html = _response_html(response)
            result["mode_used"] = "rendered"
            result["url"] = getattr(response, "url", norm_url) or norm_url
            result["status_code"] = int(getattr(response, "status", 0) or 0)
            result["headers"] = dict(getattr(response, "headers", {}) or {})
            result["content"] = html
            result["render_engine"] = "scrapling-dynamic"
            result["render_ms"] = (time.perf_counter() - started) * 1000
        except Exception as exc:
            result["error"] = f"render failed: {exc}"
            result["mode_used"] = "raw"
            result["content"] = result["raw_content"]
            result["status_code"] = raw.get("status_code")
            result["headers"] = raw.get("headers") or {}

    if extract_content and result.get("content"):
        extracted, pub_date = _extract_post_process(result["content"], result["url"])
        result["extracted_text"] = extracted
        result["publication_date"] = pub_date

    return result
