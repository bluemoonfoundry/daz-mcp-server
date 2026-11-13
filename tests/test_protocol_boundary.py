"""Architecture checks for the DazScriptServer protocol boundary."""
from __future__ import annotations

import re
from pathlib import Path


_DAZ_ROUTE = re.compile(
    r"[\"']/(?:execute|scripts|render|requests|status|health|metrics|scene/events)"
)


def test_mcp_source_does_not_construct_dazscriptserver_routes():
    """Daz endpoint URLs and wire payloads belong to dazpy, not MCP tools."""
    source_root = Path(__file__).parents[1] / "src" / "vangard_daz_mcp"
    violations = []
    for path in source_root.rglob("*.py"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _DAZ_ROUTE.search(line):
                violations.append(f"{path.relative_to(source_root)}:{line_number}: {line.strip()}")

    assert not violations, "Daz protocol routes escaped dazpy:\n" + "\n".join(violations)
