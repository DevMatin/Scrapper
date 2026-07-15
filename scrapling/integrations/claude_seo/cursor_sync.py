from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from scrapling.integrations.claude_seo.config import (
    get_agents_dir,
    get_claude_seo_root,
    get_extensions_dir,
    get_skills_dir,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sync_cursor_rules(*, force: bool = False) -> list[str]:
    rules_dir = _repo_root() / ".cursor" / "rules"
    agents_dir = rules_dir / "agents"
    rules_dir.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)

    created: list[str] = []

    agents_md = get_claude_seo_root() / "AGENTS.md"
    target_agents = rules_dir / "AGENTS-seo.md"
    _link_or_copy(agents_md, target_agents, force=force)
    created.append(str(target_agents))

    for skill_dir in sorted(get_skills_dir().glob("*/SKILL.md")):
        skill_name = skill_dir.parent.name
        target = rules_dir / f"seo-{skill_name}.mdc"
        _link_or_copy(skill_dir, target, force=force)
        created.append(str(target))

    for agent_file in sorted(get_agents_dir().glob("*.md")):
        target = agents_dir / agent_file.name
        _link_or_copy(agent_file, target, force=force)
        created.append(str(target))

    hooks_src = get_claude_seo_root() / "hooks"
    hooks_dst = _repo_root() / ".cursor" / "hooks"
    if hooks_src.is_dir():
        hooks_dst.mkdir(parents=True, exist_ok=True)
        for item in hooks_src.iterdir():
            target = hooks_dst / item.name
            _link_or_copy(item, target, force=force)
            created.append(str(target))

    return created


def _link_or_copy(src: Path, dst: Path, *, force: bool) -> None:
    if not src.exists():
        return
    if dst.exists() or dst.is_symlink():
        if force:
            dst.unlink()
        else:
            return
    try:
        os.symlink(src.resolve(), dst)
    except OSError:
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def install_extension(name: str) -> subprocess.CompletedProcess[str]:
    ext_dir = get_extensions_dir() / name
    install_sh = ext_dir / "install.sh"
    if not install_sh.is_file():
        raise FileNotFoundError(f"Extension install script not found: {install_sh}")
    return subprocess.run(["bash", str(install_sh)], capture_output=True, text=True, check=False)


def list_extensions() -> list[str]:
    if not get_extensions_dir().is_dir():
        return []
    return sorted(p.name for p in get_extensions_dir().iterdir() if p.is_dir())
