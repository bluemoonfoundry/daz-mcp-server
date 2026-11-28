"""A too-old Daz Studio plugin is reported where users and the AI see it."""

import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, patch

import dazpy
import dazpy.exceptions as daz_exc
import pytest
from fastmcp.exceptions import ToolError

from daz_mcp_server import _compat
from daz_mcp_server._client import DAZ_HOST, DAZ_PORT

TARGET = f"{DAZ_HOST}:{DAZ_PORT}"


def _check(compatible=True, version="2.12.0", instance="i1"):
    return dazpy.VersionCheck(
        server_url="http://localhost:18811",
        server_version=version,
        min_server_version="2.12",
        client_version=dazpy.__version__,
        server_instance_id=instance,
        compatible=compatible,
        message=None if compatible is not False else "plugin too old",
    )


@pytest.fixture(autouse=True)
def _reset():
    _compat.reset()
    yield
    _compat.reset()


def test_summary_before_any_check():
    s = _compat.summary()
    assert s["compatible"] is None
    assert s["plugin_version"] is None
    assert s["target"] == TARGET
    assert s["min_plugin_version"] == dazpy.MIN_SERVER_VERSION
    assert s["dazpy_version"] == dazpy.__version__


def test_incompatible_note():
    _compat.record(_check(False, "2.11.0"))
    note = _compat.incompatible_note()
    for part in ("2.11.0", dazpy.MIN_SERVER_VERSION, TARGET, "daz-script-server/releases"):
        assert part in note
    assert _compat.summary()["compatible"] is False


def test_note_clears_after_compatible_check():
    _compat.record(_check(False, "2.11.0"))
    _compat.record(_check(True, "2.12.0", "i2"))
    assert _compat.incompatible_note() is None


def test_take_unannounced_once_per_plugin():
    old = _check(False, "2.11.0", "i1")
    _compat.record(old)
    _compat.record(old)
    assert _compat.take_unannounced() is old
    assert _compat.take_unannounced() is None
    newer_run = _check(False, "2.11.0", "i2")
    _compat.record(newer_run)
    assert _compat.take_unannounced() is newer_run


def test_compatible_check_is_never_announced():
    _compat.record(_check(True))
    assert _compat.take_unannounced() is None


def test_record_thread_safe():
    checks = [_check(True), _check(False, "2.11.0")]

    def worker():
        for i in range(100):
            _compat.record(checks[i % 2])

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert _compat.latest() in checks


def test_daz_status_includes_compatibility():
    from daz_mcp_server.tools import utility

    client = MagicMock()
    client.status = AsyncMock(return_value={"running": True, "version": "2.12.0"})
    with patch.object(utility, "get_async_daz_client", return_value=client):
        result = asyncio.run(utility.daz_status())
    assert result["running"] is True
    assert result["plugin_compatibility"]["target"] == TARGET


def test_inspect_scene_only_when_incompatible():
    from daz_mcp_server.tools import workflow

    with patch.object(workflow, "daz_scene_info", AsyncMock(return_value={"nodes": 3})):
        _compat.record(_check(True))
        assert "plugin_compatibility" not in asyncio.run(workflow.daz_inspect_scene())
        _compat.record(_check(False, "2.11.0", "i2"))
        result = asyncio.run(workflow.daz_inspect_scene())
    assert result["nodes"] == 3
    assert result["plugin_compatibility"]["compatible"] is False


def test_404_error_carries_note():
    from daz_mcp_server._errors import handle_dazpy_error

    err = daz_exc.ServerResponseError("Unknown route", status_code=404)
    _compat.record(_check(False, "2.11.0"))
    with pytest.raises(ToolError) as exc:
        handle_dazpy_error(err)
    assert "older than the required" in str(exc.value)
    _compat.record(_check(True, "2.12.0", "i2"))
    with pytest.raises(ToolError) as exc:
        handle_dazpy_error(err)
    assert "older than the required" not in str(exc.value)


def test_non_404_error_has_no_note():
    from daz_mcp_server._errors import handle_dazpy_error

    _compat.record(_check(False, "2.11.0"))
    with pytest.raises(ToolError) as exc:
        handle_dazpy_error(daz_exc.ServerResponseError("boom", status_code=500))
    assert "older than the required" not in str(exc.value)


def test_sync_client_wired_to_record():
    from daz_mcp_server import _client

    saved = _client._daz_client
    _client._daz_client = None
    try:
        client = _client.get_daz_client()
        assert client._versions._callback is _compat.record
    finally:
        _client._daz_client = saved


def test_lifespan_wires_async_client(monkeypatch):
    from daz_mcp_server import _mcp

    seen = {}

    class FakeClient:
        def __init__(self, **kwargs):
            seen.update(kwargs)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return None

    monkeypatch.setattr(_mcp, "AsyncDazClient", FakeClient)
    monkeypatch.setattr(_mcp, "_register_scripts", AsyncMock())

    async def run():
        async with _mcp._lifespan(_mcp.mcp):
            pass

    asyncio.run(run())
    assert seen["on_version_check"] is _compat.record


def test_middleware_announces_once():
    from daz_mcp_server._compat import CompatibilityMiddleware

    ctx = MagicMock()
    ctx.fastmcp_context.warning = AsyncMock()
    call_next = AsyncMock(return_value="result")
    mw = CompatibilityMiddleware()
    _compat.record(_check(False, "2.11.0"))
    assert asyncio.run(mw.on_call_tool(ctx, call_next)) == "result"
    asyncio.run(mw.on_call_tool(ctx, call_next))
    ctx.fastmcp_context.warning.assert_awaited_once_with("plugin too old")


def test_middleware_announces_after_tool_error():
    from daz_mcp_server._compat import CompatibilityMiddleware

    ctx = MagicMock()
    ctx.fastmcp_context.warning = AsyncMock()
    call_next = AsyncMock(side_effect=ToolError("404"))
    _compat.record(_check(False, "2.11.0"))
    with pytest.raises(ToolError):
        asyncio.run(CompatibilityMiddleware().on_call_tool(ctx, call_next))
    ctx.fastmcp_context.warning.assert_awaited_once()


def test_middleware_registered():
    from daz_mcp_server._compat import CompatibilityMiddleware
    from daz_mcp_server._mcp import mcp

    assert any(isinstance(m, CompatibilityMiddleware) for m in mcp.middleware)
