"""Map dazpy and httpx exceptions to FastMCP ToolError."""
from __future__ import annotations

import os

from fastmcp.exceptions import ToolError

import dazpy.exceptions as daz_exc

from ._client import DAZ_TIMEOUT, TOKEN_FILE


def handle_dazpy_error(exc: Exception) -> None:
    """Re-raise a dazpy exception as a ToolError with a helpful message.

    Call this inside an except block:  handle_dazpy_error(exc)
    The function always raises; it never returns normally.
    """
    if isinstance(exc, daz_exc.ConnectionError):
        raise ToolError(
            "Cannot connect to DAZ Studio. Ensure DAZ Studio is running with "
            "the DazScriptServer plugin active."
        ) from exc
    if isinstance(exc, daz_exc.TimeoutError):
        raise ToolError(
            f"Request timed out after {DAZ_TIMEOUT}s. "
            "Increase the timeout by setting the DAZ_TIMEOUT environment variable."
        ) from exc
    if isinstance(exc, daz_exc.AuthenticationError):
        source = (
            "DAZ_API_TOKEN environment variable" if os.environ.get("DAZ_API_TOKEN") else TOKEN_FILE
        )
        raise ToolError(
            f"Authentication failed. Verify the API token in: {source}"
        ) from exc
    if isinstance(exc, daz_exc.NodeNotFoundError):
        raise ToolError(str(exc)) from exc
    if isinstance(exc, daz_exc.DazBusyError):
        raise ToolError(
            f"DAZ Studio is busy ({exc.reason}). Try again in a few seconds."
        ) from exc
    if isinstance(exc, (daz_exc.ScriptRuntimeError, daz_exc.ScriptSyntaxError)):
        raise ToolError(exc.diagnostic) from exc
    if isinstance(exc, daz_exc.ServerResponseError):
        raise ToolError(str(exc)) from exc
    raise exc
