from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_env() -> None:
    env_path = _repo_root() / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@lru_cache(maxsize=1)
def get_claude_seo_root() -> Path:
    load_env()
    configured = os.environ.get("SCRAPPER_SEO_HOME") or os.environ.get("CLAUDE_SEO_ROOT")
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = _repo_root() / path
    else:
        path = _repo_root() / "claude-seo-main"
    if not path.is_dir():
        raise FileNotFoundError(f"claude-seo vendor not found: {path}")
    return path.resolve()


def get_scripts_dir() -> Path:
    return get_claude_seo_root() / "scripts"


def get_scrapper_seo_config_dir() -> Path:
    load_env()
    configured = os.environ.get("SCRAPPER_SEO_CONFIG")
    if configured:
        path = Path(configured).expanduser()
    else:
        path = Path.home() / ".config" / "scrapper-seo"
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def get_skills_dir() -> Path:
    return get_claude_seo_root() / "skills"


def get_agents_dir() -> Path:
    return get_claude_seo_root() / "agents"


def get_extensions_dir() -> Path:
    return get_claude_seo_root() / "extensions"


def get_drift_dir() -> Path:
    path = get_scrapper_seo_config_dir() / "drift"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_google_api_key() -> str | None:
    load_env()
    return (
        os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GOOGLE_MAPS_API_KEY")
        or _read_json_key(get_scrapper_seo_config_dir() / "google-api.json", "api_key")
    )


def _read_json_key(path: Path, key: str) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    value = data.get(key)
    return str(value) if value else None


def ensure_config_layout() -> dict[str, Path]:
    root = get_scrapper_seo_config_dir()
    paths = {
        "root": root,
        "google_api": root / "google-api.json",
        "backlinks_api": root / "backlinks-api.json",
        "dataforseo_costs": root / "dataforseo-costs.json",
        "drift": get_drift_dir(),
    }
    for name in ("google-api.json", "backlinks-api.json", "dataforseo-costs.json"):
        p = root / name
        if not p.exists():
            p.write_text("{}\n", encoding="utf-8")
    return paths
