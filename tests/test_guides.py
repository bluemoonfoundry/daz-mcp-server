"""Agent guides ship inside the package and are served to the AI."""

import asyncio
import re
from pathlib import Path

from daz_mcp_server._guides import GUIDE_NAMES, guide_index, read_guide
from daz_mcp_server._mcp import mcp
from daz_mcp_server.tools.utility import daz_script_help

PKG = Path(__file__).resolve().parent.parent / "src" / "daz_mcp_server"


def test_every_guide_reads():
    assert GUIDE_NAMES == ("actors", "cinema", "daz_studio", "dazscript", "recipe", "scene")
    for name in GUIDE_NAMES:
        assert read_guide(name).lstrip().startswith("#"), name


def test_unknown_guide_raises_keyerror():
    try:
        read_guide("nope")
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def test_guide_index_lists_every_guide():
    index = guide_index()
    for name in GUIDE_NAMES:
        assert f"daz://guide/{name}" in index


def test_guides_resources_registered():
    resources = asyncio.run(mcp.list_resources(run_middleware=False))
    templates = asyncio.run(mcp.list_resource_templates(run_middleware=False))
    assert "daz://guides" in [str(r.uri) for r in resources]
    assert "daz://guide/{name}" in [str(t.uri_template) for t in templates]


def test_help_tool_serves_guides():
    assert asyncio.run(daz_script_help("guide:recipe")) == read_guide("recipe")
    assert "daz://guide/recipe" in asyncio.run(daz_script_help("guides"))
    unknown = asyncio.run(daz_script_help("guide:nope"))
    assert "Unknown" in unknown and "recipe" in unknown


def test_no_stale_skill_references():
    stale, bad = [], []
    for path in PKG.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".md", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "SKILL_" in text:
            stale.append(path.name)
        bad += [m for m in re.findall(r"daz://guide/([a-z_]+)", text) if m not in GUIDE_NAMES]
    assert stale == []
    assert bad == []


def _doc_texts():
    dev_doc = PKG.parent.parent / "SKILL_DEVELOPMENT.md"
    yield "SKILL_DEVELOPMENT.md", dev_doc.read_text(encoding="utf-8")
    for name in GUIDE_NAMES:
        yield f"guides/{name}.md", read_guide(name)


def test_docs_name_only_registered_tools_and_arguments():
    import inspect

    import daz_mcp_server.tools  # noqa: F401  # pylint: disable=unused-import  # registers every tool

    tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
    unknown, bad_kwargs = [], []
    for doc, text in _doc_texts():
        for name in sorted(set(re.findall(r"\bdaz_[a-z0-9_]+", text)) - {"daz_mcp_server"}):
            if name not in tools:
                unknown.append(f"{doc}: {name}")
        for name, args in re.findall(r"\b(daz_[a-z0-9_]+)\(([^()]*)\)", text):
            if name in tools:
                params = inspect.signature(tools[name].fn).parameters
                bad_kwargs += [f"{doc}: {name}({kw}=)"
                               for kw in re.findall(r"\b([a-z_]\w*)\s*=", args) if kw not in params]
    assert unknown == []
    assert bad_kwargs == []
