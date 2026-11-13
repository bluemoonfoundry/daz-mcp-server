"""Mock tests for Phase 6.13 Strand-Based Hair tools: daz_create_strand_hair
and daz_list_strand_hair_nodes.

All tests use respx to intercept HTTP at the transport layer — no DAZ Studio
or DazScriptServer required.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
import respx
import httpx

from dazpy.aio import AsyncDazClient
from vangard_daz_mcp._client import set_async_daz_client
from vangard_daz_mcp.tools.hair import (
    daz_create_strand_hair,
    daz_list_strand_hair_nodes,
)

BASE_URL = "http://localhost:18811"


def _ok(result):
    return httpx.Response(
        200,
        json={"success": True, "result": result, "output": [], "error": None},
    )


def _fail(error):
    return httpx.Response(
        200,
        json={"success": False, "result": None, "output": [], "error": error},
    )


def _async_submitted(request_id: str) -> httpx.Response:
    return httpx.Response(
        202,
        json={
            "request_id": request_id,
            "status": "queued",
            "submitted_at": "2026-04-08T12:00:00.000",
        },
    )


@pytest_asyncio.fixture(autouse=True)
async def daz_client():
    """Provide the protocol client (respx patches its internal transport)."""
    # check_version=False keeps the version probe out of the recorded calls.
    async with AsyncDazClient(
        host="localhost", port=18811, token="", check_version=False
    ) as client:
        set_async_daz_client(client)
        yield client
    set_async_daz_client(None)


@pytest.fixture
def mock_daz():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


class TestCreateStrandHair:
    async def test_submits_via_async_endpoint(self, mock_daz):
        """daz_create_strand_hair must never block synchronously on the
        confirmation-dialog script — verify it posts to /async, not /execute."""
        route = mock_daz.post("/scripts/vangard-create-strand-hair/async").mock(
            return_value=_async_submitted("hair-abc123")
        )
        result = await daz_create_strand_hair("Genesis 8 Female")
        assert route.called
        assert result["request_id"] == "hair-abc123"
        assert result["status"] == "queued"

    async def test_passes_target_node_label(self, mock_daz):
        captured = {}

        def capture(request):
            import json as _json
            captured.update(_json.loads(request.content))
            return _async_submitted("hair-xyz")

        mock_daz.post("/scripts/vangard-create-strand-hair/async").mock(
            side_effect=capture
        )
        await daz_create_strand_hair("Genesis 9 Male")
        assert captured["args"]["targetNodeLabel"] == "Genesis 9 Male"

    async def test_never_calls_sync_execute_endpoint(self, mock_daz):
        """Guards the async-only usage constraint: no route should exist for
        a synchronous /execute call on this script id."""
        sync_route = mock_daz.post("/scripts/vangard-create-strand-hair/execute").mock(
            return_value=_ok({"success": True})
        )
        mock_daz.post("/scripts/vangard-create-strand-hair/async").mock(
            return_value=_async_submitted("hair-guard")
        )
        await daz_create_strand_hair("Genesis 8 Female")
        assert not sync_route.called


class TestListStrandHairNodes:
    async def test_returns_nodes(self, mock_daz):
        payload = {
            "count": 1,
            "nodes": [
                {
                    "label": "Strand-Based Hair",
                    "name": "Strand_Based_Hair",
                    "target": "Genesis 8 Female",
                    "has_geometry": True,
                    "materials": ["Hair"],
                }
            ],
        }
        mock_daz.post("/scripts/vangard-list-strand-hair-nodes/execute").mock(
            return_value=_ok(payload)
        )
        result = await daz_list_strand_hair_nodes()
        assert result["count"] == 1
        assert result["nodes"][0]["target"] == "Genesis 8 Female"
        assert result["nodes"][0]["has_geometry"] is True

    async def test_empty_scene(self, mock_daz):
        mock_daz.post("/scripts/vangard-list-strand-hair-nodes/execute").mock(
            return_value=_ok({"count": 0, "nodes": []})
        )
        result = await daz_list_strand_hair_nodes()
        assert result["count"] == 0
        assert result["nodes"] == []

    async def test_script_failure_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError

        mock_daz.post("/scripts/vangard-list-strand-hair-nodes/execute").mock(
            return_value=_fail("Scene not available")
        )
        with pytest.raises(ToolError):
            await daz_list_strand_hair_nodes()
