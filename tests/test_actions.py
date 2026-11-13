"""Mock tests for Bug #14 tools: daz_find_actions, daz_erc_freeze."""

from __future__ import annotations

import pytest
import pytest_asyncio
import respx
import httpx
from fastmcp.exceptions import ToolError

from dazpy.aio import AsyncDazClient
from vangard_daz_mcp._client import set_async_daz_client
from vangard_daz_mcp._registry import _REGISTRY
from vangard_daz_mcp.tools.utility import daz_find_actions
from vangard_daz_mcp.tools.figure import daz_erc_freeze

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


class TestFindActionsScript:
    def test_uses_action_mgr_not_menubar(self):
        script = _REGISTRY["vangard-find-actions"][1]
        assert "menuBar" not in script
        assert "getActionMgr" in script
        assert "findAction" not in script or "getAction" in script
        assert "getNumActions" in script
        assert ".trigger(" not in script

    def test_erc_freeze_script_is_headless(self):
        script = _REGISTRY["vangard-erc-freeze"][1]
        assert "menuBar" not in script
        assert "DzERCFreezeAction" not in script
        assert "new DzERCFreeze()" in script
        assert "doFreeze()" in script
        assert ".trigger(" not in script
        assert "function resolveNode" in script


class TestFindActions:
    async def test_returns_matches(self, mock_daz):
        payload = {
            "query": "ERC Freeze",
            "count": 1,
            "scanned": 875,
            "truncated": False,
            "matches": [{"className": "DzERCFreezeAction", "simpleText": "ERC Freeze"}],
        }
        mock_daz.post("/scripts/vangard-find-actions/execute").mock(return_value=_ok(payload))
        result = await daz_find_actions("ERC Freeze")
        assert result["count"] == 1
        assert result["matches"][0]["className"] == "DzERCFreezeAction"

    async def test_empty_query_raises(self, mock_daz):
        mock_daz.post("/scripts/vangard-find-actions/execute").mock(
            return_value=_fail("query is required")
        )
        with pytest.raises(ToolError):
            await daz_find_actions("")


class TestErcFreeze:
    async def test_successful_freeze(self, mock_daz):
        payload = {
            "success": True,
            "controllerNode": "Genesis 8 Female",
            "controllerProperty": "MyShape",
            "propertiesFrozen": 3,
        }
        mock_daz.post("/scripts/vangard-erc-freeze/execute").mock(return_value=_ok(payload))
        result = await daz_erc_freeze("Genesis 8 Female", "MyShape")
        assert result["success"] is True
        assert result["propertiesFrozen"] == 3

    async def test_missing_controller_raises(self, mock_daz):
        mock_daz.post("/scripts/vangard-erc-freeze/execute").mock(
            return_value=_fail("Controller property not found: Ghost on Genesis 8 Female")
        )
        with pytest.raises(ToolError):
            await daz_erc_freeze("Genesis 8 Female", "Ghost")

    async def test_nothing_to_freeze_raises(self, mock_daz):
        mock_daz.post("/scripts/vangard-erc-freeze/execute").mock(
            return_value=_fail(
                "No properties to freeze (values at default?). "
                "Change morphs/transforms first."
            )
        )
        with pytest.raises(ToolError):
            await daz_erc_freeze("Genesis 8 Female", "MyShape")

    async def test_passes_freeze_nodes(self, mock_daz):
        captured = {}

        def capture(request):
            captured["json"] = request.content
            return _ok({"success": True, "propertiesFrozen": 1})

        mock_daz.post("/scripts/vangard-erc-freeze/execute").mock(side_effect=capture)
        await daz_erc_freeze(
            "Genesis 8 Female",
            "MyShape",
            freeze_nodes=["Genesis 8 Female", "head"],
        )
        body = captured["json"].decode("utf-8")
        assert "Genesis 8 Female" in body
        assert "MyShape" in body
        assert "head" in body
