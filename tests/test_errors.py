"""Unit tests for dazpy-to-ToolError error mapping in _errors.py.

Pure unit tests — no live DAZ Studio connection needed.
"""
from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

import dazpy.exceptions as daz_exc

from daz_mcp_server._errors import handle_dazpy_error


class TestHandleDazpyErrorBusy:
    """StudioBusyError/ConcurrencyLimitError map to a clear, retry-friendly ToolError."""

    def test_studio_busy_error_maps_to_tool_error_with_reason(self):
        """503 STUDIO_BUSY surfaces the server's reason text in the tool error."""
        exc = daz_exc.StudioBusyError(
            "DAZ Studio's main thread is busy; please retry shortly",
            reason="DAZ Studio is currently loading a scene",
            retry_after=2.0,
        )
        with pytest.raises(ToolError) as ctx:
            handle_dazpy_error(exc)
        message = str(ctx.value)
        assert "DAZ Studio is busy" in message
        assert "DAZ Studio is currently loading a scene" in message
        assert "Try again in a few seconds" in message

    def test_concurrency_limit_error_maps_to_tool_error_with_reason(self):
        """429 CONCURRENT_LIMIT_EXCEEDED also maps through the busy-error path."""
        exc = daz_exc.ConcurrencyLimitError(
            "Server busy: maximum concurrent requests reached, please retry",
            reason="Server busy: maximum concurrent requests reached, please retry",
            retry_after=2.0,
        )
        with pytest.raises(ToolError) as ctx:
            handle_dazpy_error(exc)
        message = str(ctx.value)
        assert "DAZ Studio is busy" in message
        assert "maximum concurrent requests reached" in message

    def test_busy_error_is_not_reported_as_script_error(self):
        """DazBusyError must never be mistaken for a script failure."""
        exc = daz_exc.StudioBusyError("busy", reason="rendering", retry_after=2.0)
        with pytest.raises(ToolError) as ctx:
            handle_dazpy_error(exc)
        assert "diagnostic" not in str(ctx.value).lower()


class TestHandleDazpyErrorExistingBehaviorUnchanged:
    """Guard against regressions to the pre-existing mappings."""

    def test_connection_error(self):
        """ConnectionError still maps to a connect-failure ToolError."""
        with pytest.raises(ToolError, match="Cannot connect to DAZ Studio"):
            handle_dazpy_error(daz_exc.ConnectionError("refused"))

    def test_authentication_error(self):
        """AuthenticationError still maps to an auth-failure ToolError."""
        with pytest.raises(ToolError, match="Authentication failed"):
            handle_dazpy_error(daz_exc.AuthenticationError("HTTP 401"))

    def test_script_runtime_error_uses_diagnostic(self):
        """ScriptRuntimeError still surfaces its line-numbered diagnostic."""
        exc = daz_exc.ScriptRuntimeError("TypeError: bad", script="bad();", request_id="r1")
        with pytest.raises(ToolError) as ctx:
            handle_dazpy_error(exc)
        assert "bad();" in str(ctx.value)

    def test_unmapped_exception_reraised_as_is(self):
        """Exceptions with no explicit mapping are re-raised unchanged."""
        exc = ValueError("not a dazpy error")
        with pytest.raises(ValueError):
            handle_dazpy_error(exc)
