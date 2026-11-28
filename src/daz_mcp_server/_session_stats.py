"""Per-session tool call statistics and the last tool error.

``SessionStatsMiddleware`` wraps every tool call, so ``daz_get_performance_stats``
and ``daz_explain_last_error`` report what actually happened in this MCP server
process instead of placeholder data. State lives in memory and resets when the
server restarts.
"""
from __future__ import annotations

import re
import threading
import time
from datetime import datetime, timezone
from typing import Any

from fastmcp.server.middleware import Middleware

_MAX_ARG_CHARS = 500
_MAX_MESSAGE_CHARS = 4000

_lock = threading.Lock()
_stats: dict[str, dict[str, float]] = {}
_last_error: dict[str, Any] | None = None  # pylint: disable=invalid-name


# (pattern, hint) pairs matched against the last error's message, in order.
ERROR_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"validation error|missing required argument|unexpected keyword argument", re.I),
     "The arguments didn't match the tool's schema. Check the parameter names "
     "and types in the tool description."),
    (re.compile(r"cannot connect|connection refused|connecterror", re.I),
     "DAZ Studio isn't reachable. Start it, check the DazScriptServer pane says "
     "the server is running, and check DAZ_HOST/DAZ_PORT."),
    (re.compile(r"authentication failed|401|unauthori[sz]ed", re.I),
     "The API token doesn't match. Set DAZ_API_TOKEN, or check the token file "
     "named in the error against the one in the DazScriptServer pane."),
    (re.compile(r"timed out|timeout", re.I),
     "The call took longer than DAZ_TIMEOUT. Long renders and simulations should "
     "use the async tools (daz_submit_job, daz_render_async) and be polled."),
    (re.compile(r"busy|rate limit|too many|429|503", re.I),
     "The server is busy or rate-limited. Wait a few seconds and retry, or raise "
     "the limits in the DazScriptServer pane."),
    (re.compile(r"ambiguous", re.I),
     "Several nodes share that label. Pass one of the listed elementIDs or a "
     "'Parent/Label' path instead."),
    (re.compile(r"node not found|no node|not found in scene", re.I),
     "No node has that label. List nodes with daz_scene_info or daz_find_nodes; "
     "labels are case-sensitive, and an elementID or 'Parent/Label' also works."),
    (re.compile(r"property not found|no property|morph not found", re.I),
     "The node has no such property. Use daz_inspect_properties or "
     "daz_search_morphs to find the exact name."),
    (re.compile(r"syntaxerror|referenceerror|typeerror|can't find variable|"
                r"is not a function|parse error", re.I),
     "The DazScript failed. Check the reported line, run daz_validate_script, and "
     "see daz_script_help for the globals and gotchas."),
    (re.compile(r"404|not found.*route|unknown route|plugin.*too old|incompatible", re.I),
     "The plugin may be older than this MCP server expects. daz_status shows the "
     "plugin version; update DazScriptServer."),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _summarize_args(arguments: dict[str, Any] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in (arguments or {}).items():
        text = repr(value)
        out[key] = text if len(text) <= _MAX_ARG_CHARS else text[:_MAX_ARG_CHARS] + "..."
    return out


def record_call(tool: str, duration_ms: float, error: BaseException | None,
                arguments: dict[str, Any] | None = None) -> None:
    """Record one finished tool call (and, on failure, the last error)."""
    global _last_error  # pylint: disable=global-statement
    with _lock:
        entry = _stats.setdefault(
            tool, {"calls": 0, "errors": 0, "total_ms": 0.0, "max_ms": 0.0}
        )
        entry["calls"] += 1
        entry["total_ms"] += duration_ms
        entry["max_ms"] = max(entry["max_ms"], duration_ms)
        if error is not None:
            entry["errors"] += 1
            message = str(error) or type(error).__name__
            _last_error = {
                "tool": tool,
                "error_type": type(error).__name__,
                "message": message[:_MAX_MESSAGE_CHARS],
                "arguments": _summarize_args(arguments),
                "at": _now(),
            }


def performance_stats() -> dict[str, Any]:
    """Per-tool call counts, error counts and durations for this session."""
    with _lock:
        tools = {
            name: {
                "calls": int(s["calls"]),
                "errors": int(s["errors"]),
                "total_ms": round(s["total_ms"], 1),
                "avg_ms": round(s["total_ms"] / s["calls"], 1) if s["calls"] else 0.0,
                "max_ms": round(s["max_ms"], 1),
            }
            for name, s in sorted(_stats.items())
        }
    return {
        "tools": tools,
        "total_calls": sum(t["calls"] for t in tools.values()),
        "total_errors": sum(t["errors"] for t in tools.values()),
    }


def last_error() -> dict[str, Any] | None:
    """A copy of the most recent tool error, or None."""
    with _lock:
        return dict(_last_error) if _last_error else None


def hints_for(message: str) -> list[str]:
    """Hints whose pattern matches ``message``."""
    return [hint for pattern, hint in ERROR_HINTS if pattern.search(message)]


def reset() -> None:
    """Clear all recorded state (tests)."""
    global _last_error  # pylint: disable=global-statement
    with _lock:
        _stats.clear()
        _last_error = None


# Tools that read this state are not counted, so asking for stats or the last
# error doesn't change them.
_SELF_TOOLS = {"daz_get_performance_stats", "daz_explain_last_error"}


class SessionStatsMiddleware(Middleware):
    """Time every tool call and remember the last one that failed."""

    async def on_call_tool(self, context, call_next):
        name = getattr(context.message, "name", "?")
        if name in _SELF_TOOLS:
            return await call_next(context)
        arguments = getattr(context.message, "arguments", None)
        start = time.perf_counter()
        try:
            result = await call_next(context)
        except Exception as exc:
            record_call(name, (time.perf_counter() - start) * 1000.0, exc, arguments)
            raise
        error = None
        if getattr(result, "is_error", False):
            error = RuntimeError(_result_text(result))
        record_call(name, (time.perf_counter() - start) * 1000.0, error, arguments)
        return result


def _result_text(result: Any) -> str:
    parts = []
    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts) or "tool reported an error"
