"""The version and tool counts stated in the docs match the package.

pyproject.toml is the source of truth for the version; the live tool registry
is the source of truth for tool counts.  Bump pyproject.toml, then fix whatever
this test names.
"""

import asyncio
import re
import tomllib
from importlib.metadata import version as installed_version
from pathlib import Path

import vangard_daz_mcp.tools  # noqa: F401  registers every tool
from vangard_daz_mcp._mcp import mcp

ROOT = Path(__file__).resolve().parent.parent
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _tools() -> list:
    return asyncio.run(mcp.list_tools())


def test_installed_package_matches_pyproject():
    assert installed_version("vangard-daz-mcp") == VERSION


def test_server_reports_the_package_version_to_clients():
    # MCP clients see this in initialize's serverInfo.version.
    assert mcp.version == VERSION


def test_readme_badge_matches():
    assert re.search(r"\*\*Version ([^*]+)\*\*", _read("README.md")).group(1) == VERSION


def test_claude_md_matches():
    assert re.search(r"\*\*Version:\*\* (\S+)", _read("CLAUDE.md")).group(1) == VERSION


def test_tool_counts_in_docs_match_the_registry():
    tools = _tools()
    modules = {t.fn.__module__.rsplit(".", 1)[-1] for t in tools}
    claude = re.search(r"\*\*Registry:\*\* (\d+) tools registered across (\d+) tool modules",
                       _read("CLAUDE.md"))
    assert (int(claude.group(1)), int(claude.group(2))) == (len(tools), len(modules))
    readme = _read("README.md")
    assert f"all {len(tools)} registered tools" in readme
    assert f"({len(tools)} tools registered;" in readme
    skill = re.search(r"imports all (\d+) tool modules \((\d+) tools total\)",
                      _read("SKILL_DEVELOPMENT.md"))
    assert (int(skill.group(1)), int(skill.group(2))) == (len(modules), len(tools))


def test_readme_module_tree_lists_every_module_with_its_count():
    readme = _read("README.md")
    counts: dict[str, int] = {}
    for t in _tools():
        mod = t.fn.__module__.rsplit(".", 1)[-1]
        counts[mod] = counts.get(mod, 0) + 1
    for mod, n in counts.items():
        line = re.search(rf"│\s+[├└]── {mod}\.py\s+#.*\((\d+) tools?\)", readme)
        assert line, f"README module tree has no line for tools/{mod}.py with a tool count"
        assert int(line.group(1)) == n, f"tools/{mod}.py: README says {line.group(1)}, registry has {n}"
