"""The package is published and run under one name: daz-mcp-server."""

import importlib.metadata
import importlib.util
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_import_name():
    import daz_mcp_server  # noqa: F401

    assert importlib.util.find_spec("vangard_daz_mcp") is None


def test_server_name():
    from daz_mcp_server._mcp import mcp

    assert mcp.name == "daz-mcp-server"


def test_console_script():
    scripts = {ep.name: ep.value for ep in importlib.metadata.entry_points(group="console_scripts")}
    assert scripts.get("daz-mcp-server") == "daz_mcp_server.server:main"
    assert "vangard-daz-mcp" not in scripts


def test_authors_have_no_email():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["authors"] == [{"name": "Blue Moon Foundry"}]
