"""Mock tests for Phase 6.8 tool: daz_run_transfer_utility.

All tests use respx to intercept HTTP at the transport layer — no DAZ Studio
or DazScriptServer required.
"""

from __future__ import annotations

import json

import pytest
import pytest_asyncio
import respx
import httpx

from dazpy.aio import AsyncDazClient
from vangard_daz_mcp._client import set_async_daz_client
from vangard_daz_mcp.tools.wardrobe import daz_run_transfer_utility

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


class TestRunTransferUtility:
    async def test_successful_transfer(self, mock_daz):
        payload = {"success": True, "source": "Genesis 8 Female", "target": "Custom Hair Prop"}
        mock_daz.post("/scripts/vangard-run-transfer-utility/execute").mock(
            return_value=_ok(payload)
        )
        result = await daz_run_transfer_utility("Genesis 8 Female", "Custom Hair Prop")
        assert result["success"] is True
        assert result["source"] == "Genesis 8 Female"
        assert result["target"] == "Custom Hair Prop"

    async def test_source_not_found_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-run-transfer-utility/execute").mock(
            return_value=_fail("Source node not found: Ghost")
        )
        with pytest.raises(ToolError):
            await daz_run_transfer_utility("Ghost", "Cape")

    async def test_target_not_found_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-run-transfer-utility/execute").mock(
            return_value=_fail("Target node not found: Ghost")
        )
        with pytest.raises(ToolError):
            await daz_run_transfer_utility("Genesis 9", "Ghost")

    async def test_do_transfer_failure_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-run-transfer-utility/execute").mock(
            return_value=_fail(
                "DzTransferUtility.doTransfer() returned false (source: 'A', target: 'B')"
            )
        )
        with pytest.raises(ToolError):
            await daz_run_transfer_utility("A", "B")

    async def test_default_args_sent(self, mock_daz):
        captured = {}

        def capture(request, route):
            captured["args"] = json.loads(request.content).get("args", {})
            return _ok({"success": True, "source": "Genesis 9", "target": "Bracelet"})

        mock_daz.post("/scripts/vangard-run-transfer-utility/execute").mock(side_effect=capture)
        await daz_run_transfer_utility("Genesis 9", "Bracelet")
        args = captured["args"]
        assert args["sourceLabel"] == "Genesis 9"
        assert args["targetLabel"] == "Bracelet"
        assert args["transferBinding"] is True
        assert args["transferMorphs"] is True
        assert args["transferUVs"] is False
        assert args["transferMaterialGroups"] is False
        assert args["transferFaceGroups"] is False
        assert args["fitToFigure"] is True
        assert args["parentToFigure"] is False
        assert args["mergeHierarchies"] is False

    async def test_custom_flags_sent(self, mock_daz):
        captured = {}

        def capture(request, route):
            captured["args"] = json.loads(request.content).get("args", {})
            return _ok({"success": True, "source": "Genesis 8 Female", "target": "Cape"})

        mock_daz.post("/scripts/vangard-run-transfer-utility/execute").mock(side_effect=capture)
        await daz_run_transfer_utility(
            "Genesis 8 Female",
            "Cape",
            transfer_binding=True,
            transfer_morphs=False,
            transfer_uvs=True,
            parent_to_figure=True,
        )
        args = captured["args"]
        assert args["transferMorphs"] is False
        assert args["transferUVs"] is True
        assert args["parentToFigure"] is True
