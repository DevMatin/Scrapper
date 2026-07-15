from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from scrapling.integrations.claude_seo.config import load_env

LLM_ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "business_type": {
            "type": "string",
            "enum": ["local", "saas", "ecommerce", "publisher", "agency"],
        },
        "summary": {
            "type": "object",
            "properties": {
                "narrative": {"type": "string"},
                "top_findings": {"type": "array", "items": {"type": "string"}},
                "quick_wins": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["narrative", "top_findings", "quick_wins"],
            "additionalProperties": False,
        },
        "eeat": {
            "type": "object",
            "properties": {
                "experience": {"type": "integer"},
                "expertise": {"type": "integer"},
                "authoritativeness": {"type": "integer"},
                "trustworthiness": {"type": "integer"},
            },
            "required": ["experience", "expertise", "authoritativeness", "trustworthiness"],
            "additionalProperties": False,
        },
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "score": {"type": "integer"},
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "severity": {
                                    "type": "string",
                                    "enum": ["Critical", "High", "Medium", "Low", "Info"],
                                },
                                "description": {"type": "string"},
                                "recommendation": {"type": "string"},
                            },
                            "required": ["title", "severity", "description", "recommendation"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["name", "score", "findings"],
                "additionalProperties": False,
            },
        },
        "action_plan": {
            "type": "object",
            "properties": {
                "phases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "timeframe": {"type": "string"},
                            "items": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["name", "timeframe", "items"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["phases"],
            "additionalProperties": False,
        },
    },
    "required": ["business_type", "summary", "eeat", "categories", "action_plan"],
    "additionalProperties": False,
}


def get_azure_openai_config() -> dict[str, str] | None:
    load_env()
    base = os.environ.get("AZURE_OPENAI_BASE_URL") or os.environ.get("AZURE_OPENAI_ENDPOINT")
    key = os.environ.get("AZURE_OPENAI_API_KEY")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    if base and key and deployment:
        endpoint = base.rstrip("/")
        for suffix in ("/openai", "/openai/"):
            if endpoint.endswith(suffix):
                endpoint = endpoint[: -len(suffix)]
        return {
            "endpoint": endpoint,
            "api_key": key,
            "deployment": deployment,
            "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        }
    return None


def _azure_auth_headers(api_key: str) -> list[dict[str, str]]:
    return [
        {"api-key": api_key, "Content-Type": "application/json"},
        {"Ocp-Apim-Subscription-Key": api_key, "Content-Type": "application/json"},
    ]


def _azure_chat_json_rest(
    system: str,
    user: str,
    *,
    model: str,
    response_format: dict[str, Any],
) -> dict[str, Any]:
    azure = get_azure_openai_config()
    if not azure:
        raise RuntimeError("Azure OpenAI not configured")

    payload: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": response_format,
    }
    body = json.dumps(payload).encode()
    versions = [azure["api_version"], "2024-08-01-preview", "2024-02-15-preview"]
    last_error: Exception | None = None

    for api_version in dict.fromkeys(versions):
        url = (
            f"{azure['endpoint']}/openai/deployments/{model}/chat/completions"
            f"?api-version={api_version}"
        )
        for headers in _azure_auth_headers(azure["api_key"]):
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode())
                content = data["choices"][0]["message"]["content"] or "{}"
                result = json.loads(content)
                result["model"] = data.get("model") or model
                result["generated_at"] = datetime.now(timezone.utc).isoformat()
                return result
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode()
                last_error = RuntimeError(f"Azure OpenAI HTTP {exc.code}: {detail}")
            except Exception as exc:
                last_error = exc

    if last_error:
        raise last_error
    raise RuntimeError("Azure OpenAI request failed")


def get_openai_api_key() -> str | None:
    load_env()
    return os.environ.get("OPENAI_API_KEY")


def get_openai_model() -> str:
    load_env()
    return os.environ.get("OPENAI_MODEL") or "gpt-4.1-mini"


def get_llm_model() -> str:
    azure = get_azure_openai_config()
    if azure:
        return azure["deployment"]
    return get_openai_model()


def _create_chat_client():
    try:
        from openai import AzureOpenAI, OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package required (pip install scrapling[seo])") from exc

    azure = get_azure_openai_config()
    if azure:
        return (
            AzureOpenAI(
                azure_endpoint=azure["endpoint"],
                api_key=azure["api_key"],
                api_version=azure["api_version"],
            ),
            azure["deployment"],
        )

    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError(
            "LLM not configured: set AZURE_OPENAI_BASE_URL, AZURE_OPENAI_API_KEY, "
            "AZURE_OPENAI_DEPLOYMENT or OPENAI_API_KEY"
        )
    return OpenAI(api_key=api_key), get_openai_model()


def chat_json(system: str, user: str, *, model: str | None = None) -> dict[str, Any]:
    response_format: dict[str, Any] = {
        "type": "json_schema",
        "json_schema": {
            "name": "llm_analysis",
            "strict": True,
            "schema": LLM_ANALYSIS_SCHEMA,
        },
    }

    azure = get_azure_openai_config()
    if azure:
        return _azure_chat_json_rest(
            system,
            user,
            model=model or azure["deployment"],
            response_format=response_format,
        )

    client, default_model = _create_chat_client()
    response = client.chat.completions.create(
        model=model or default_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=response_format,
    )
    content = response.choices[0].message.content or "{}"
    result = json.loads(content)
    result["model"] = response.model or (model or default_model)
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    return result
