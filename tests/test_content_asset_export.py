"""Mock tests for Phase 6.11 tool: daz_save_prop_asset.

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
from vangard_daz_mcp.tools.content import daz_save_prop_asset

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


class TestSavePropAsset:
    async def test_successful_save(self, mock_daz):
        payload = {
            "success": True,
            "node": "My Prop",
            "outputPath": "C:/Library/Props/MyProduct/My Prop.duf",
            "baseDataPath": "C:/Library",
            "vendorName": "MyStudio",
            "productName": "My Product",
            "itemName": "My Prop",
        }
        mock_daz.post("/scripts/vangard-save-prop-asset/execute").mock(return_value=_ok(payload))
        result = await daz_save_prop_asset(
            "My Prop",
            "C:/Library/Props/MyProduct/My Prop.duf",
            vendor_name="MyStudio",
            product_name="My Product",
        )
        assert result["success"] is True
        assert result["node"] == "My Prop"
        assert result["baseDataPath"] == "C:/Library"

    async def test_node_not_found_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-save-prop-asset/execute").mock(
            return_value=_fail("Node not found: Ghost")
        )
        with pytest.raises(ToolError):
            await daz_save_prop_asset("Ghost", "C:/Library/Props/Ghost.duf")

    async def test_output_path_outside_content_dir_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-save-prop-asset/execute").mock(
            return_value=_fail(
                "outputPath must be inside a configured DAZ content directory. "
                "outputPath=D:/Elsewhere/prop.duf ; configured directories: C:/Library"
            )
        )
        with pytest.raises(ToolError):
            await daz_save_prop_asset("My Prop", "D:/Elsewhere/prop.duf")

    async def test_do_save_failure_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-save-prop-asset/execute").mock(
            return_value=_fail(
                "DzNodeSupportAssetFilter.doSave failed (error code 98) for node My Prop"
            )
        )
        with pytest.raises(ToolError):
            await daz_save_prop_asset("My Prop", "C:/Library/Props/My Prop.duf")

    async def test_default_args_sent(self, mock_daz):
        captured = {}

        def capture(request, route):
            captured["args"] = json.loads(request.content).get("args", {})
            return _ok({"success": True, "node": "My Prop"})

        mock_daz.post("/scripts/vangard-save-prop-asset/execute").mock(side_effect=capture)
        await daz_save_prop_asset("My Prop", "C:/Library/Props/My Prop.duf")
        args = captured["args"]
        assert args["nodeLabel"] == "My Prop"
        assert args["outputPath"] == "C:/Library/Props/My Prop.duf"
        assert args["vendorName"] == "Author"
        assert args["productName"] == "Product"
        # Optional fields omitted entirely when not passed — not sent as null/None.
        assert "itemName" not in args
        assert "category" not in args
        assert "smartParent" not in args

    async def test_custom_flags_sent(self, mock_daz):
        captured = {}

        def capture(request, route):
            captured["args"] = json.loads(request.content).get("args", {})
            return _ok({"success": True, "node": "My Prop"})

        mock_daz.post("/scripts/vangard-save-prop-asset/execute").mock(side_effect=capture)
        await daz_save_prop_asset(
            "My Prop",
            "C:/Library/Props/My Prop.duf",
            vendor_name="MyStudio",
            product_name="My Product",
            item_name="Custom Item",
            category="Props/Furniture",
            compatibility_base="Genesis 9",
            compatible_with="Genesis 8",
            smart_parent=True,
            write_geometry=True,
            write_parameters=False,
            write_uvs=True,
            force_unique_ids=True,
            compress_output=False,
        )
        args = captured["args"]
        assert args["vendorName"] == "MyStudio"
        assert args["productName"] == "My Product"
        assert args["itemName"] == "Custom Item"
        assert args["category"] == "Props/Furniture"
        assert args["compatibilityBase"] == "Genesis 9"
        assert args["compatibleWith"] == "Genesis 8"
        assert args["smartParent"] is True
        assert args["writeGeometry"] is True
        assert args["writeParameters"] is False
        assert args["writeUvs"] is True
        assert args["forceUniqueIds"] is True
        assert args["compressOutput"] is False
