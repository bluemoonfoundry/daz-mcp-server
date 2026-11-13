"""Mock tests for Phase 6.9 tools: daz_get/set_dforce_surface_property.

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
from vangard_daz_mcp.tools.wardrobe import (
    daz_get_dforce_surface_properties,
    daz_set_dforce_surface_property,
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


class TestGetDforceSurfaceProperties:
    async def test_returns_properties(self, mock_daz):
        payload = {
            "node": "Genesis 8 Female",
            "material": "Torso",
            "property_count": 2,
            "properties": [
                {"name": "Collision Offset", "label": "Collision Offset",
                 "type": "numeric", "value": 0.2},
                {"name": "Self Collide", "label": "Self Collide",
                 "type": "numeric", "value": 1},
            ],
        }
        mock_daz.post("/scripts/vangard-get-dforce-surface-properties/execute").mock(
            return_value=_ok(payload)
        )
        result = await daz_get_dforce_surface_properties("Genesis 8 Female", "Torso")
        assert result["material"] == "Torso"
        assert result["property_count"] == 2

    async def test_no_provider_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-get-dforce-surface-properties/execute").mock(
            return_value=_fail(
                "No dForce simulation settings for material 'Torso' on 'Genesis 8 Female'"
            )
        )
        with pytest.raises(ToolError):
            await daz_get_dforce_surface_properties("Genesis 8 Female", "Torso")

    async def test_material_name_omitted_by_default(self, mock_daz):
        captured = {}

        def capture(request, route):
            captured["args"] = json.loads(request.content).get("args", {})
            return _ok({
                "node": "Hair", "material": "Fibers",
                "property_count": 0, "properties": [],
            })

        mock_daz.post("/scripts/vangard-get-dforce-surface-properties/execute").mock(
            side_effect=capture
        )
        await daz_get_dforce_surface_properties("Hair")
        assert "materialName" not in captured["args"]
        assert captured["args"]["nodeLabel"] == "Hair"

    async def test_material_name_sent_when_given(self, mock_daz):
        captured = {}

        def capture(request, route):
            captured["args"] = json.loads(request.content).get("args", {})
            return _ok({
                "node": "Outfit", "material": "Fabric",
                "property_count": 0, "properties": [],
            })

        mock_daz.post("/scripts/vangard-get-dforce-surface-properties/execute").mock(
            side_effect=capture
        )
        await daz_get_dforce_surface_properties("Outfit", "Fabric")
        assert captured["args"]["materialName"] == "Fabric"


class TestSetDforceSurfaceProperty:
    async def test_successful_set(self, mock_daz):
        payload = {
            "success": True,
            "node": "Outfit",
            "material": "Fabric",
            "property": "Collision Offset",
            "old_value": 0.2,
            "new_value": 0.5,
        }
        mock_daz.post("/scripts/vangard-set-dforce-surface-property/execute").mock(
            return_value=_ok(payload)
        )
        result = await daz_set_dforce_surface_property(
            "Outfit", "Collision Offset", 0.5, "Fabric"
        )
        assert result["success"] is True
        assert result["new_value"] == 0.5

    async def test_property_not_found_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-set-dforce-surface-property/execute").mock(
            return_value=_fail(
                "Property 'Bogus' not found on dForce surface 'Torso'. Available: Friction, ..."
            )
        )
        with pytest.raises(ToolError):
            await daz_set_dforce_surface_property("Genesis 8 Female", "Bogus", 1.0)

    async def test_args_without_material_name(self, mock_daz):
        captured = {}

        def capture(request, route):
            captured["args"] = json.loads(request.content).get("args", {})
            return _ok({
                "success": True, "node": "Hair", "material": "Fibers",
                "property": "Dynamics Strength", "old_value": 1.0, "new_value": 0.8,
            })

        mock_daz.post("/scripts/vangard-set-dforce-surface-property/execute").mock(
            side_effect=capture
        )
        await daz_set_dforce_surface_property("Hair", "Dynamics Strength", 0.8)
        args = captured["args"]
        assert "materialName" not in args
        assert args["propertyName"] == "Dynamics Strength"
        assert args["value"] == 0.8

    async def test_args_with_material_name(self, mock_daz):
        captured = {}

        def capture(request, route):
            captured["args"] = json.loads(request.content).get("args", {})
            return _ok({
                "success": True, "node": "Outfit", "material": "Fabric",
                "property": "Self Collide", "old_value": 0, "new_value": 1,
            })

        mock_daz.post("/scripts/vangard-set-dforce-surface-property/execute").mock(
            side_effect=capture
        )
        await daz_set_dforce_surface_property(
            "Outfit", "Self Collide", 1, material_name="Fabric"
        )
        assert captured["args"]["materialName"] == "Fabric"
