"""Integration tests — async request lifecycle and management.

Tools covered
-------------
- daz_list_requests
- daz_get_request_status
- daz_get_request_result
- daz_cancel_request
- daz_render_async (start-then-cancel, to avoid waiting for full render)
- daz_wait_for_request

Renders are cancelled immediately after starting to avoid long test times.
"""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_cancel_request,
    daz_get_request_result,
    daz_get_request_status,
    daz_list_requests,
    daz_render_async,
    daz_wait_for_request,
)


# ---------------------------------------------------------------------------
# daz_list_requests
# ---------------------------------------------------------------------------

class TestListRequests:
    async def test_returns_dict(self, live_client):
        result = await daz_list_requests()
        assert isinstance(result, dict)

    async def test_has_requests_list(self, live_client):
        result = await daz_list_requests()
        requests = result.get("requests", result.get("items", []))
        assert isinstance(requests, list)

    async def test_filter_by_status(self, live_client):
        result = await daz_list_requests(status_filter="completed")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_render_async + daz_get_request_status + daz_cancel_request
# ---------------------------------------------------------------------------

class TestAsyncRenderLifecycle:
    async def test_start_and_cancel(self, live_client, tmp_path):
        """Start an async render then cancel immediately — no waiting."""
        output = str(tmp_path / "async_test.png").replace("\\", "/")
        start_result = await daz_render_async(output_path=output)
        assert isinstance(start_result, dict)

        request_id = start_result.get("request_id", start_result.get("id", ""))
        assert request_id, f"No request_id in result: {start_result}"

        # Check status
        status_result = await daz_get_request_status(request_id)
        assert isinstance(status_result, dict)
        status = status_result.get("status", "")
        assert status in ("queued", "running", "completed", "cancelled", "failed")

        # Cancel
        cancel_result = await daz_cancel_request(request_id)
        assert isinstance(cancel_result, dict)

    async def test_status_of_unknown_request_raises(self, live_client):
        with pytest.raises((ToolError, Exception)):
            await daz_get_request_status("nonexistent-request-id-xyz-999")

    async def test_cancel_unknown_request_raises(self, live_client):
        with pytest.raises((ToolError, Exception)):
            await daz_cancel_request("nonexistent-request-id-xyz-999")


# ---------------------------------------------------------------------------
# daz_get_request_result
# ---------------------------------------------------------------------------

class TestGetRequestResult:
    async def test_result_of_cancelled_request(self, live_client, tmp_path):
        """Start, cancel, then check result — should return cancelled status."""
        output = str(tmp_path / "result_test.png").replace("\\", "/")
        start = await daz_render_async(output_path=output)
        request_id = start.get("request_id", start.get("id", ""))
        if not request_id:
            pytest.skip("Could not get request_id from async render start")

        await daz_cancel_request(request_id)

        result = await daz_get_request_result(request_id, wait=False)
        assert isinstance(result, dict)

    async def test_unknown_request_raises(self, live_client):
        with pytest.raises((ToolError, Exception)):
            await daz_get_request_result("nonexistent-request-id-xyz-999", wait=False)


# ---------------------------------------------------------------------------
# daz_wait_for_request
# ---------------------------------------------------------------------------

class TestWaitForRequest:
    async def test_wait_for_cancelled_returns_quickly(self, live_client, tmp_path):
        """Cancel a request then wait — should return immediately with cancelled state."""
        output = str(tmp_path / "wait_test.png").replace("\\", "/")
        start = await daz_render_async(output_path=output)
        request_id = start.get("request_id", start.get("id", ""))
        if not request_id:
            pytest.skip("Could not get request_id from async render start")

        await daz_cancel_request(request_id)
        result = await daz_wait_for_request(request_id, timeout_seconds=10)
        assert isinstance(result, dict)

    async def test_unknown_request_raises(self, live_client):
        with pytest.raises((ToolError, Exception)):
            await daz_wait_for_request("nonexistent-request-id-xyz-999", timeout_seconds=5)
