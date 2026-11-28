"""Session stats middleware, daz_get_performance_stats and daz_explain_last_error."""
from __future__ import annotations

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from daz_mcp_server import _session_stats
from daz_mcp_server._mcp import mcp as server_mcp
from daz_mcp_server.tools.utility import daz_explain_last_error, daz_get_performance_stats


@pytest.fixture(autouse=True)
def _reset():
    _session_stats.reset()
    yield
    _session_stats.reset()


def _server() -> FastMCP:
    app = FastMCP("stats-test")
    app.add_middleware(_session_stats.SessionStatsMiddleware())

    @app.tool()
    async def ok_tool(x: int) -> int:
        return x + 1

    @app.tool()
    async def failing_tool(label: str) -> str:
        raise ToolError(f"Node not found: {label}")

    @app.tool()
    async def daz_get_performance_stats() -> dict:  # pylint: disable=redefined-outer-name
        return _session_stats.performance_stats()

    return app


async def test_middleware_counts_calls_and_errors():
    async with Client(_server()) as client:
        await client.call_tool("ok_tool", {"x": 1})
        await client.call_tool("ok_tool", {"x": 2})
        with pytest.raises(Exception):
            await client.call_tool("failing_tool", {"label": "Genesis 9"})
        # Reading the stats is not itself counted.
        await client.call_tool("daz_get_performance_stats", {})

    stats = await daz_get_performance_stats()
    assert stats["total_calls"] == 3
    assert stats["total_errors"] == 1
    assert stats["tools"]["ok_tool"]["calls"] == 2
    assert stats["tools"]["ok_tool"]["errors"] == 0
    assert stats["tools"]["failing_tool"]["calls"] == 1
    assert stats["tools"]["failing_tool"]["errors"] == 1
    assert "daz_get_performance_stats" not in stats["tools"]
    for entry in stats["tools"].values():
        assert entry["max_ms"] >= entry["avg_ms"] >= 0


async def test_explain_last_error_reports_the_failure_and_a_matching_hint():
    async with Client(_server()) as client:
        with pytest.raises(Exception):
            await client.call_tool("failing_tool", {"label": "Genesis 9"})
        await client.call_tool("ok_tool", {"x": 1})  # a later success keeps the error

    result = await daz_explain_last_error()
    err = result["last_error"]
    assert err["tool"] == "failing_tool"
    assert "Node not found: Genesis 9" in err["message"]
    assert err["arguments"] == {"label": "'Genesis 9'"}
    assert err["at"]
    assert any("daz_scene_info" in h for h in result["hints"])


async def test_explain_last_error_with_no_error_lists_common_hints():
    result = await daz_explain_last_error()
    assert result["last_error"] is None
    assert len(result["hints"]) == len(_session_stats.ERROR_HINTS)


async def test_explain_last_error_unmatched_message_gets_generic_hint():
    _session_stats.record_call("t", 1.0, RuntimeError("something odd"))
    result = await daz_explain_last_error()
    assert result["last_error"]["error_type"] == "RuntimeError"
    assert len(result["hints"]) == 1


def test_long_arguments_are_truncated():
    _session_stats.record_call("t", 1.0, RuntimeError("x"), {"script": "a" * 5000})
    assert len(_session_stats.last_error()["arguments"]["script"]) < 600


@pytest.mark.parametrize("message, needle", [
    ("Cannot connect to DAZ Studio. Ensure DAZ Studio is running", "isn't reachable"),
    ("Authentication failed. Verify the API token", "token"),
    ("Request timed out after 30s", "async"),
    ("DAZ Studio is busy (queue full). Try again", "busy"),
    ("Ambiguous node label 'Hair': 2 matches", "elementID"),
    ("1 validation error for call[x]\nfoo\n  Missing required argument", "schema"),
    ("ReferenceError: Can't find variable: args (line 3)", "daz_validate_script"),
])
def test_hint_table(message, needle):
    assert any(needle in h for h in _session_stats.hints_for(message))


def test_removed_tools_are_gone():
    from daz_mcp_server.tools import utility  # pylint: disable=import-outside-toplevel

    for gone in ("daz_start_recording", "daz_stop_recording", "daz_list_macros",
                 "daz_replay_macro", "daz_suggest_next_action"):
        assert not hasattr(utility, gone)


def test_server_installs_the_stats_middleware():
    assert any(isinstance(m, _session_stats.SessionStatsMiddleware)
               for m in server_mcp.middleware)
