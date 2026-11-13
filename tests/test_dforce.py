"""Mock tests for Phase 6.2 dForce tools: daz_add_dforce_dynamic_surface and
daz_set/get_dforce_influence_weights.

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
    daz_add_dforce_dynamic_surface,
    daz_get_dforce_influence_weights,
    daz_set_dforce_influence_weights,
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


class TestAddDforceDynamicSurface:
    async def test_adds_modifier(self, mock_daz):
        payload = {
            "success": True,
            "node": "Tablecloth",
            "already_present": False,
            "modifier": "DzDForceModifier",
        }
        mock_daz.post("/scripts/vangard-add-dforce-dynamic-surface/execute").mock(
            return_value=_ok(payload)
        )
        result = await daz_add_dforce_dynamic_surface("Tablecloth")
        assert result["success"] is True
        assert result["already_present"] is False
        assert result["modifier"] == "DzDForceModifier"

    async def test_already_present_is_noop(self, mock_daz):
        payload = {
            "success": True,
            "node": "Outfit",
            "already_present": True,
            "modifier": "DzDForceModifier",
        }
        mock_daz.post("/scripts/vangard-add-dforce-dynamic-surface/execute").mock(
            return_value=_ok(payload)
        )
        result = await daz_add_dforce_dynamic_surface("Outfit")
        assert result["already_present"] is True

    async def test_node_not_found_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-add-dforce-dynamic-surface/execute").mock(
            return_value=_fail("Node not found: Ghost")
        )
        with pytest.raises(ToolError):
            await daz_add_dforce_dynamic_surface("Ghost")

    async def test_sends_node_label_in_args(self, mock_daz):
        captured = {}

        def capture(request, route):
            body = json.loads(request.content)
            captured["args"] = body.get("args", {})
            return _ok({
                "success": True,
                "node": "Cape",
                "already_present": False,
                "modifier": "DzDForceModifier",
            })

        mock_daz.post("/scripts/vangard-add-dforce-dynamic-surface/execute").mock(
            side_effect=capture
        )
        await daz_add_dforce_dynamic_surface("Cape")
        assert captured["args"]["nodeLabel"] == "Cape"


class TestSetDforceInfluenceWeights:
    async def test_pins_listed_vertices(self, mock_daz):
        payload = {
            "success": True,
            "node": "Hair Strand",
            "vertex_count": 26,
            "default_weight": 1.0,
            "overridden_count": 2,
        }
        mock_daz.post("/scripts/vangard-set-dforce-influence-weights/execute").mock(
            return_value=_ok(payload)
        )
        result = await daz_set_dforce_influence_weights(
            "Hair Strand", {0: 0.0, 1: 0.0}
        )
        assert result["success"] is True
        assert result["overridden_count"] == 2

    async def test_sends_vertex_weights_and_default(self, mock_daz):
        captured = {}

        def capture(request, route):
            body = json.loads(request.content)
            captured["args"] = body.get("args", {})
            return _ok({
                "success": True,
                "node": "Cape",
                "vertex_count": 10,
                "default_weight": 0.0,
                "overridden_count": 1,
            })

        mock_daz.post("/scripts/vangard-set-dforce-influence-weights/execute").mock(
            side_effect=capture
        )
        await daz_set_dforce_influence_weights(
            "Cape", {3: 1.0}, default_weight=0.0
        )
        assert captured["args"]["nodeLabel"] == "Cape"
        assert captured["args"]["defaultWeight"] == 0.0
        assert captured["args"]["vertexWeights"] == {"3": 1.0}

    async def test_omits_vertex_weights_when_none_given(self, mock_daz):
        captured = {}

        def capture(request, route):
            body = json.loads(request.content)
            captured["args"] = body.get("args", {})
            return _ok({
                "success": True,
                "node": "Outfit",
                "vertex_count": 500,
                "default_weight": 1.0,
                "overridden_count": 0,
            })

        mock_daz.post("/scripts/vangard-set-dforce-influence-weights/execute").mock(
            side_effect=capture
        )
        await daz_set_dforce_influence_weights("Outfit")
        assert "vertexWeights" not in captured["args"]

    async def test_no_modifier_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-set-dforce-influence-weights/execute").mock(
            return_value=_fail("No dForce modifier found on 'Plain Prop'.")
        )
        with pytest.raises(ToolError):
            await daz_set_dforce_influence_weights("Plain Prop", {0: 0.0})


class TestGetDforceInfluenceWeights:
    async def test_returns_weights(self, mock_daz):
        payload = {
            "success": True,
            "node": "Hair Strand",
            "has_influence_weights": True,
            "vertex_count": 4,
            "weights": [0.0, 0.0, 1.0, 1.0],
        }
        mock_daz.post("/scripts/vangard-get-dforce-influence-weights/execute").mock(
            return_value=_ok(payload)
        )
        result = await daz_get_dforce_influence_weights("Hair Strand")
        assert result["has_influence_weights"] is True
        assert result["weights"] == [0.0, 0.0, 1.0, 1.0]

    async def test_no_weights_set_yet(self, mock_daz):
        payload = {
            "success": True,
            "node": "Outfit",
            "has_influence_weights": False,
            "weights": [],
        }
        mock_daz.post("/scripts/vangard-get-dforce-influence-weights/execute").mock(
            return_value=_ok(payload)
        )
        result = await daz_get_dforce_influence_weights("Outfit")
        assert result["has_influence_weights"] is False
        assert result["weights"] == []
