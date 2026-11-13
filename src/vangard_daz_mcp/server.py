"""MCP server wrapping the DazScriptServer HTTP API for DAZ Studio.

Entry point: ``vangard-daz-mcp`` (defined in pyproject.toml).

All tool registrations happen when ``vangard_daz_mcp.tools`` is imported;
each sub-module decorates its functions with ``@mcp.tool()`` on the shared
FastMCP instance from ``_mcp.py``. ``@mcp.tool()`` is transparent (it
returns the original async function, not a wrapper), so re-exporting those
names here via ``import *`` gives back the same directly-callable
coroutine functions the modules define — this is the compatibility surface
any external caller importing from ``vangard_daz_mcp.server`` directly
(rather than reaching into ``vangard_daz_mcp.tools.<module>``) expects.
Without it, every name below raises ImportError from here even though the
tool is correctly registered on the live ``mcp`` instance. The test suite
imports from each ``vangard_daz_mcp.tools.<module>`` directly instead (see
SKILL_DEVELOPMENT.md), not from here.
"""

from ._mcp import mcp  # noqa: F401 — creates the FastMCP instance + lifespan
from . import tools  # noqa: F401 — registers all @mcp.tool() functions  # pylint: disable=unused-import
from ._profile import configure_profile


ACTIVE_PROFILE = configure_profile(mcp)

# Re-export every tool function so `from vangard_daz_mcp.server import daz_x`
# keeps working regardless of which tools/<module>.py it actually lives in.
from .tools.spatial import *  # noqa: F401,F403
from .tools.transform import *  # noqa: F401,F403
from .tools.scene import *  # noqa: F401,F403
from .tools.figure import *  # noqa: F401,F403
from .tools.morph import *  # noqa: F401,F403
from .tools.camera_light import *  # noqa: F401,F403
from .tools.render import *  # noqa: F401,F403
from .tools.animation import *  # noqa: F401,F403
from .tools.material import *  # noqa: F401,F403
from .tools.utility import *  # noqa: F401,F403
from .tools.content import *  # noqa: F401,F403
from .tools.cinematic import *  # noqa: F401,F403
from .tools.wardrobe import *  # noqa: F401,F403
from .tools.hair import *  # noqa: F401,F403


def main() -> None:
    """Run the FastMCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
