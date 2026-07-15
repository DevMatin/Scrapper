from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from scrapling.integrations.claude_seo import fetch_adapter
from scrapling.integrations.claude_seo.config import get_scripts_dir, _repo_root
from scrapling.integrations.claude_seo.registry import SeoCapability, get_capability


@contextmanager
def patched_seo_environment() -> Iterator[None]:
    scripts_dir = str(get_scripts_dir())
    inserted = False
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
        inserted = True

    saved: dict[str, Any] = {}
    try:
        import render_page as rp  # noqa: E402
        import fetch_page as fp  # noqa: E402

        saved["render_page"] = rp.render_page
        saved["fetch_page"] = fp.fetch_page
        rp.render_page = fetch_adapter.render_page
        fp.fetch_page = fetch_adapter.fetch_page
        sys.modules["render_page"] = rp
        sys.modules["fetch_page"] = fp
        yield
    finally:
        if "render_page" in saved:
            sys.modules["render_page"].render_page = saved["render_page"]
        if "fetch_page" in saved:
            sys.modules["fetch_page"].fetch_page = saved["fetch_page"]
        if inserted:
            try:
                sys.path.remove(scripts_dir)
            except ValueError:
                pass


def import_seo_module(module_name: str):
    with patched_seo_environment():
        if module_name in sys.modules:
            mod = sys.modules[module_name]
            return importlib.reload(mod)
        return importlib.import_module(module_name)


def call_module_function(module_name: str, function_name: str, *args: Any, **kwargs: Any) -> Any:
    mod = import_seo_module(module_name)
    func = getattr(mod, function_name)
    return func(*args, **kwargs)


def run_capability(
    capability_id: str,
    *,
    url: str | None = None,
    text: str | None = None,
    extra_args: list[str] | None = None,
) -> Any:
    cap = get_capability(capability_id)

    if capability_id == "parse_html" and text is not None:
        return call_module_function("parse_html", "parse_html", text, url)
    if capability_id == "content_quality" and text is not None:
        return call_module_function("content_quality", "analyse", text)
    if capability_id == "content_verify" and text is not None:
        return call_module_function("content_verify", "verify", text)
    if capability_id == "preload_check" and text is not None:
        return call_module_function("preload_check", "analyse", text, {})
    if capability_id in ("render_page", "fetch_page") and url:
        fn = fetch_adapter.render_page if capability_id == "render_page" else fetch_adapter.fetch_page
        return fn(url)

    if url and cap.requires_url:
        import subprocess
        import tempfile

        script_path = get_scripts_dir() / cap.script
        argv_tail = [url]
        if extra_args:
            argv_tail.extend(extra_args)
        if "--json" not in argv_tail:
            argv_tail.append("--json")

        wrapper = Path(tempfile.gettempdir()) / f"scrapper_seo_{capability_id}.py"
        wrapper.write_text(
            f"""import sys, runpy
sys.path.insert(0, {str(get_scripts_dir())!r})
repo = {str(_repo_root())!r}
if repo not in sys.path:
    sys.path.insert(0, repo)
from scrapling.integrations.claude_seo import fetch_adapter as fa
import render_page as rp
import fetch_page as fp
rp.render_page = fa.render_page
fp.fetch_page = fa.fetch_page
sys.argv = [{str(script_path)!r}] + {argv_tail!r}
runpy.run_path({str(script_path)!r}, run_name='__main__')
""",
            encoding="utf-8",
        )
        proc = subprocess.run([sys.executable, str(wrapper)], capture_output=True, text=True)
        if proc.stdout.strip():
            import json

            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError:
                return {"output": proc.stdout, "stderr": proc.stderr}
        return {"error": proc.stderr or "empty output", "stdout": proc.stdout}

    raise ValueError(f"Cannot run capability {capability_id} with given inputs")
