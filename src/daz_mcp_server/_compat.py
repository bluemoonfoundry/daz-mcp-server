"""Daz Studio plugin compatibility, as reported by dazpy's version checks.

Both dazpy clients call :func:`record` after every completed check (dazpy's
``on_version_check``). Tools read the result: ``daz_status`` always reports it,
``daz_inspect_scene`` and 404-type tool errors mention it when the plugin is too
old, and :class:`CompatibilityMiddleware` sends one MCP log warning per too-old
running plugin.
"""
from __future__ import annotations

import sys
import threading
from typing import Any

import dazpy
from dazpy import VersionCheck
from fastmcp.server.middleware import Middleware

from ._client import DAZ_HOST, DAZ_PORT

_RELEASES_URL = "https://github.com/bluemoonfoundry/daz-script-server/releases"

_lock = threading.Lock()
_latest: VersionCheck | None = None  # pylint: disable=invalid-name
_printed: set[tuple] = set()
_announced: set[tuple] = set()


def _key(check: VersionCheck) -> tuple:
    return (check.server_url, check.server_instance_id, check.server_version)


def record(check: VersionCheck) -> None:
    """dazpy ``on_version_check`` callback: store the latest check."""
    global _latest  # pylint: disable=global-statement
    with _lock:
        _latest = check
        first = check.compatible is False and _key(check) not in _printed
        if first:
            _printed.add(_key(check))
    if first:
        print(f"daz-mcp-server: {check.message}", file=sys.stderr, flush=True)


def latest() -> VersionCheck | None:
    """The most recent completed check, or ``None``."""
    return _latest


def summary() -> dict[str, Any]:
    """Plugin compatibility as reported to tools."""
    check = _latest
    return {
        "target": f"{DAZ_HOST}:{DAZ_PORT}",
        "plugin_version": check.server_version if check else None,
        "min_plugin_version": dazpy.MIN_SERVER_VERSION,
        "dazpy_version": dazpy.__version__,
        "compatible": check.compatible if check else None,
        "message": incompatible_note(),
    }


def incompatible_note() -> str | None:
    """Upgrade advice when the latest check found the plugin too old."""
    check = _latest
    if check is None or check.compatible is not False:
        return None
    return (
        f"The Daz Studio plugin at {DAZ_HOST}:{DAZ_PORT} is {check.server_version}, "
        f"older than the required {check.min_server_version}; upgrade it ({_RELEASES_URL})."
    )


def take_unannounced() -> VersionCheck | None:
    """The latest incompatible check, once per running plugin (for the MCP log)."""
    with _lock:
        check = _latest
        if check is None or check.compatible is not False or _key(check) in _announced:
            return None
        _announced.add(_key(check))
        return check


def reset() -> None:
    """Forget everything (tests)."""
    global _latest  # pylint: disable=global-statement
    with _lock:
        _latest = None
        _printed.clear()
        _announced.clear()


class CompatibilityMiddleware(Middleware):
    """After each tool call, log a too-old plugin to the MCP client once."""

    async def on_call_tool(self, context, call_next):
        try:
            return await call_next(context)
        finally:
            check = take_unannounced()
            if check is not None:
                try:
                    await context.fastmcp_context.warning(check.message)
                except Exception:  # pylint: disable=broad-exception-caught
                    pass  # logging must never break a tool call
