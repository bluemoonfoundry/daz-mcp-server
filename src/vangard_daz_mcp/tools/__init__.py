"""Tool modules for the Vangard DAZ MCP server.

Importing each module here registers its @mcp.tool() decorators.
server.py does: from . import tools
"""

from . import spatial       # noqa: F401
from . import transform     # noqa: F401
from . import scene         # noqa: F401
from . import figure        # noqa: F401
from . import morph         # noqa: F401
from . import camera_light  # noqa: F401
from . import render        # noqa: F401
from . import animation     # noqa: F401
from . import material      # noqa: F401
from . import utility       # noqa: F401
from . import content       # noqa: F401
from . import cinematic     # noqa: F401
from . import wardrobe      # noqa: F401
from . import workflow      # noqa: F401
