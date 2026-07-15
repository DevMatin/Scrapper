from __future__ import annotations

import json
import os
import uuid
import urllib.error
import urllib.request
from typing import Any

from scrapling.integrations.claude_seo.config import load_env


def _supabase_url() -> str | None:
    load_env()
    return os.environ.get("SUPABASE_URL")


def _supabase_write_key() -> str | None:
    load_env()
    return os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")


def _supabase_read_key() -> str | None:
    load_env()
    return os.environ.get("SUPABASE_KEY")


def save_audit(
    report: dict[str, Any],
    *,
    lead_id: str | None = None,
    llm_analysis: dict[str, Any] | None = None,
) -> str | None:
    url_base = _supabase_url()
    key = _supabase_write_key()
    if not url_base or not key:
        return None

    audit_id = str(uuid.uuid4())
    scores = report.get("scores") or {}
    payload: dict[str, Any] = {
        "id": audit_id,
        "lead_id": lead_id,
        "url": report.get("url"),
        "health_score": scores.get("health"),
        "on_page_score": scores.get("on_page"),
        "content_score": scores.get("content"),
        "technical_score": scores.get("technical"),
        "schema_score": scores.get("schema"),
        "images_score": scores.get("images"),
        "issues": report.get("issues") or [],
        "report": report,
    }
    if llm_analysis is not None:
        payload["llm_analysis"] = llm_analysis

    use_service_role = key == os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    req = urllib.request.Request(
        f"{url_base.rstrip('/')}/rest/v1/seo_audits",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Prefer": "return=representation" if use_service_role else "return=minimal",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if use_service_role:
                rows = json.loads(resp.read().decode())
                if rows:
                    return rows[0].get("id")
            return audit_id
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"Supabase insert failed: {detail}") from exc
    return None


def fetch_leads_with_websites(limit: int = 100) -> list[dict[str, Any]]:
    url_base = _supabase_url()
    key = _supabase_read_key()
    if not url_base or not key:
        return []

    query = f"{url_base.rstrip('/')}/rest/v1/leads?select=id,name,website,branche,ort&website=not.is.null&limit={limit}"
    req = urllib.request.Request(
        query,
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_leads_without_recent_audit(limit: int = 100, days: int = 7) -> list[dict[str, Any]]:
    url_base = _supabase_url()
    key = _supabase_read_key()
    if not url_base or not key:
        return []

    all_leads = fetch_leads_with_websites(limit=limit * 3)
    if not all_leads:
        return []

    lead_ids = [l["id"] for l in all_leads if l.get("id")]
    if not lead_ids:
        return all_leads[:limit]

    ids_filter = ",".join(lead_ids)
    audit_query = (
        f"{url_base.rstrip('/')}/rest/v1/seo_audits"
        f"?select=lead_id,scanned_at&lead_id=in.({ids_filter})"
        f"&order=scanned_at.desc"
    )
    req = urllib.request.Request(
        audit_query,
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            audits = json.loads(resp.read().decode())
    except urllib.error.HTTPError:
        return all_leads[:limit]

    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent_ids: set[str] = set()
    for audit in audits:
        lead_id = audit.get("lead_id")
        scanned = audit.get("scanned_at")
        if not lead_id or not scanned:
            continue
        try:
            ts = datetime.fromisoformat(scanned.replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts >= cutoff:
            recent_ids.add(lead_id)

    filtered = [l for l in all_leads if l.get("id") not in recent_ids]
    return filtered[:limit]
