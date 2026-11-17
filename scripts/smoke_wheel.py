"""Smoke-test an *installed* daz-mcp-server (run with ``python -I``).

Checks that the installed package registers its tools and can read its bundled
guides and data files. Never runs the server lifespan, so it never contacts
Daz Studio. Exit code 0 on success, 1 on failure.
"""
from __future__ import annotations

import asyncio
import sys


def main() -> int:
    from daz_mcp_server._guides import GUIDE_NAMES, read_guide
    from daz_mcp_server.server import mcp
    from daz_mcp_server.tools import utility

    if "site-packages" not in (utility.__file__ or ""):
        print(f"FAIL: imported from the source tree, not an install: {utility.__file__}")
        return 1
    tools = asyncio.run(mcp.list_tools(run_middleware=False))
    if not tools:
        print("FAIL: no tools registered")
        return 1
    for name in GUIDE_NAMES:
        if not read_guide(name).strip():
            print(f"FAIL: guide {name} is empty")
            return 1
    if not utility._DAZSCRIPT_DOCS:  # pylint: disable=protected-access
        print("FAIL: dazscript_docs.json not loaded")
        return 1
    print(f"OK {len(tools)} tools, {len(GUIDE_NAMES)} guides")
    return 0


if __name__ == "__main__":
    sys.exit(main())
