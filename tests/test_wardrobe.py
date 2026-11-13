"""Mock tests for Phase 6.1 wardrobe tools.

Tools covered
-------------
- daz_list_fitted_items
- daz_fit_clothing
- daz_unfit_item

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
from vangard_daz_mcp.tools.wardrobe import daz_list_fitted_items, daz_fit_clothing, daz_unfit_item

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
    async with AsyncDazClient(host="localhost", port=18811, token="") as client:
        set_async_daz_client(client)
        yield client
    set_async_daz_client(None)


@pytest.fixture
def mock_daz():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


# ---------------------------------------------------------------------------
# daz_list_fitted_items
# ---------------------------------------------------------------------------

class TestListFittedItems:
    async def test_returns_dict(self, mock_daz):
        payload = {
            "figure": "Genesis 9",
            "fitted_count": 2,
            "fitted_items": [
                {
                    "label": "Sci-Fi Bodysuit",
                    "name": "SciFiBodysuit",
                    "type": "clothing",
                    "element_id": 42,
                },
                {"label": "Boots", "name": "Boots", "type": "prop", "element_id": 43},
            ],
        }
        mock_daz.post("/scripts/vangard-list-fitted-items/execute").mock(return_value=_ok(payload))
        result = await daz_list_fitted_items("Genesis 9")
        assert result["figure"] == "Genesis 9"
        assert result["fitted_count"] == 2

    async def test_empty_wardrobe(self, mock_daz):
        payload = {"figure": "Genesis 9", "fitted_count": 0, "fitted_items": []}
        mock_daz.post("/scripts/vangard-list-fitted-items/execute").mock(return_value=_ok(payload))
        result = await daz_list_fitted_items("Genesis 9")
        assert result["fitted_count"] == 0
        assert result["fitted_items"] == []

    async def test_items_have_type_field(self, mock_daz):
        items = [
            {"label": "Hair", "name": "Hair", "type": "hair", "element_id": 10},
            {"label": "Dress", "name": "Dress", "type": "clothing", "element_id": 11},
            {"label": "Sword", "name": "Sword", "type": "prop", "element_id": 12},
        ]
        mock_daz.post("/scripts/vangard-list-fitted-items/execute").mock(
            return_value=_ok({"figure": "Genesis 9", "fitted_count": 3, "fitted_items": items})
        )
        result = await daz_list_fitted_items("Genesis 9")
        types = {i["type"] for i in result["fitted_items"]}
        assert types == {"hair", "clothing", "prop"}

    async def test_figure_not_found_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-list-fitted-items/execute").mock(
            return_value=_fail("Figure not found: Ghost")
        )
        with pytest.raises(ToolError):
            await daz_list_fitted_items("Ghost")

    async def test_sends_figure_label_in_args(self, mock_daz):
        captured = {}

        def capture(request, route):
            import json
            body = json.loads(request.content)
            captured["args"] = body.get("args", {})
            return _ok({"figure": "Genesis 9", "fitted_count": 0, "fitted_items": []})

        mock_daz.post("/scripts/vangard-list-fitted-items/execute").mock(side_effect=capture)
        await daz_list_fitted_items("Genesis 9")
        assert captured["args"]["figureLabel"] == "Genesis 9"


# ---------------------------------------------------------------------------
# daz_fit_clothing
# ---------------------------------------------------------------------------

class TestFitClothing:
    async def test_successful_fit(self, mock_daz):
        payload = {
            "success": True,
            "clothing": "Sci-Fi Bodysuit",
            "figure": "Genesis 9",
            "method": "setFollowTarget",
        }
        mock_daz.post("/scripts/vangard-fit-clothing/execute").mock(return_value=_ok(payload))
        result = await daz_fit_clothing("Sci-Fi Bodysuit", "Genesis 9")
        assert result["success"] is True
        assert result["clothing"] == "Sci-Fi Bodysuit"
        assert result["figure"] == "Genesis 9"

    async def test_method_field_present(self, mock_daz):
        payload = {
            "success": True,
            "clothing": "Hat",
            "figure": "Genesis 9",
            "method": "addNodeChild",
        }
        mock_daz.post("/scripts/vangard-fit-clothing/execute").mock(return_value=_ok(payload))
        result = await daz_fit_clothing("Hat", "Genesis 9")
        assert "method" in result

    async def test_clothing_not_found_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-fit-clothing/execute").mock(
            return_value=_fail("Clothing node not found: NonExistent")
        )
        with pytest.raises(ToolError):
            await daz_fit_clothing("NonExistent", "Genesis 9")

    async def test_figure_not_found_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-fit-clothing/execute").mock(
            return_value=_fail("Figure not found: Ghost")
        )
        with pytest.raises(ToolError):
            await daz_fit_clothing("Dress", "Ghost")

    async def test_sends_correct_args(self, mock_daz):
        captured = {}

        def capture(request, route):
            import json
            body = json.loads(request.content)
            captured["args"] = body.get("args", {})
            return _ok({
                "success": True,
                "clothing": "Dress",
                "figure": "G9",
                "method": "setFollowTarget",
            })

        mock_daz.post("/scripts/vangard-fit-clothing/execute").mock(side_effect=capture)
        await daz_fit_clothing("Dress", "G9")
        assert captured["args"]["clothingLabel"] == "Dress"
        assert captured["args"]["figureLabel"] == "G9"


# ---------------------------------------------------------------------------
# daz_unfit_item
# ---------------------------------------------------------------------------

class TestUnfitItem:
    async def test_successful_unfit(self, mock_daz):
        payload = {
            "success": True,
            "item": "Sci-Fi Bodysuit",
            "previous_figure": "Genesis 9",
            "actions": ["cleared follow target"],
        }
        mock_daz.post("/scripts/vangard-unfit-item/execute").mock(return_value=_ok(payload))
        result = await daz_unfit_item("Sci-Fi Bodysuit")
        assert result["success"] is True
        assert result["previous_figure"] == "Genesis 9"

    async def test_actions_list_present(self, mock_daz):
        payload = {
            "success": True,
            "item": "Hat",
            "previous_figure": "Genesis 9",
            "actions": ["detached from parent"],
        }
        mock_daz.post("/scripts/vangard-unfit-item/execute").mock(return_value=_ok(payload))
        result = await daz_unfit_item("Hat")
        assert isinstance(result["actions"], list)
        assert len(result["actions"]) > 0

    async def test_no_relationship_still_succeeds(self, mock_daz):
        payload = {
            "success": True,
            "item": "Free Prop",
            "previous_figure": None,
            "actions": ["no fitting relationship found"],
        }
        mock_daz.post("/scripts/vangard-unfit-item/execute").mock(return_value=_ok(payload))
        result = await daz_unfit_item("Free Prop")
        assert result["success"] is True
        assert result["previous_figure"] is None

    async def test_item_not_found_raises(self, mock_daz):
        from fastmcp.exceptions import ToolError
        mock_daz.post("/scripts/vangard-unfit-item/execute").mock(
            return_value=_fail("Item not found: Ghost")
        )
        with pytest.raises(ToolError):
            await daz_unfit_item("Ghost")

    async def test_sends_item_label_in_args(self, mock_daz):
        captured = {}

        def capture(request, route):
            import json
            body = json.loads(request.content)
            captured["args"] = body.get("args", {})
            return _ok({
                "success": True, "item": "Boots",
                "previous_figure": None, "actions": []
            })

        mock_daz.post("/scripts/vangard-unfit-item/execute").mock(side_effect=capture)
        await daz_unfit_item("Boots")
        assert captured["args"]["itemLabel"] == "Boots"
