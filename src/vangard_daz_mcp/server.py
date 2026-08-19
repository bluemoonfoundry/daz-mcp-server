"""MCP server wrapping the DazScriptServer HTTP API for DAZ Studio.

Entry point: ``vangard-daz-mcp`` (defined in pyproject.toml).

All tool registrations happen when ``vangard_daz_mcp.tools`` is imported;
each sub-module decorates its functions with ``@mcp.tool()`` on the shared
FastMCP instance from ``_mcp.py``.
"""

from ._mcp import mcp  # noqa: F401 — creates the FastMCP instance + lifespan
from . import tools  # noqa: F401 — registers all @mcp.tool() functions  # pylint: disable=unused-import
from ._profile import configure_profile


ACTIVE_PROFILE = configure_profile(mcp)


def main() -> None:
    """Run the FastMCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
