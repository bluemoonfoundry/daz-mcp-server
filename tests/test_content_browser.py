"""Mock tests for daz_search_content and daz_load_product.

These tests never touch DAZ Studio or the content browser server —
respx intercepts all HTTP calls at the transport layer.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
import respx
import httpx
from dazpy.aio import AsyncDazClient

from vangard_daz_mcp._client import (
    CONTENT_BROWSER_URL,
    set_content_browser_client,
    set_async_daz_client,
)
from vangard_daz_mcp.tools.content import daz_search_content, daz_load_product


DAZ_BASE = "http://localhost:18811"
CB_BASE = CONTENT_BROWSER_URL  # http://localhost:8080 by default


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def clients():
    """Wire both HTTP clients into the server module for every test."""
    async with (
        AsyncDazClient(host="localhost", port=18811, token="") as daz_client,
        httpx.AsyncClient(base_url=CB_BASE) as cb_client,
    ):
        set_async_daz_client(daz_client)
        set_content_browser_client(cb_client)
        yield
    set_async_daz_client(None)
    set_content_browser_client(None)


@pytest.fixture
def mock_cb():
    """respx mock router scoped to the content browser base URL."""
    with respx.mock(base_url=CB_BASE, assert_all_called=False) as router:
        yield router


# ---------------------------------------------------------------------------
# daz_search_content
# ---------------------------------------------------------------------------

class TestSearchContent:
    async def test_returns_results(self, mock_cb):
        payload = {
            "results": [
                {
                    "sku": "PA-12345",
                    "name": "Sci-Fi Armor G9",
                    "description": "Futuristic armor set",
                    "compatible_figures": ["Genesis 9"],
                    "tags": ["sci-fi", "armor"],
                    "store_url": "https://www.daz3d.com/sci-fi-armor-g9",
                }
            ]
        }
        mock_cb.post("/api/v1/search").mock(return_value=httpx.Response(200, json=payload))
        result = await daz_search_content("sci-fi armor for Genesis 9", max_results=5)
        assert result == payload

    async def test_passes_query_and_max_results(self, mock_cb):
        captured = {}

        def capture(request, route):
            import json
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"results": []})

        mock_cb.post("/api/v1/search").mock(side_effect=capture)
        await daz_search_content("fantasy sword", max_results=3)
        assert captured["body"]["query"] == "fantasy sword"
        assert captured["body"]["max_results"] == 3

    async def test_unavailable_when_connect_error(self, mock_cb):
        mock_cb.post("/api/v1/search").mock(side_effect=httpx.ConnectError("refused"))
        result = await daz_search_content("anything")
        assert result["available"] is False
        assert "not reachable" in result["reason"]

    async def test_unavailable_on_non_200(self, mock_cb):
        mock_cb.post("/api/v1/search").mock(return_value=httpx.Response(503))
        result = await daz_search_content("anything")
        assert result["available"] is False
        assert "503" in result["reason"]

    async def test_empty_results(self, mock_cb):
        mock_cb.post("/api/v1/search").mock(return_value=httpx.Response(200, json={"results": []}))
        result = await daz_search_content("no match here")
        assert result == {"results": []}

    async def test_default_max_results_is_10(self, mock_cb):
        captured = {}

        def capture(request, route):
            import json
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"results": []})

        mock_cb.post("/api/v1/search").mock(side_effect=capture)
        await daz_search_content("test")
        assert captured["body"]["max_results"] == 10


# ---------------------------------------------------------------------------
# daz_load_product
# ---------------------------------------------------------------------------

PRODUCT_RECORD = {
    "sku": "PA-99999",
    "name": "Fantasy Sword",
    "path": "/content/Props/Weapons/FantasySword.duf",
}


class TestLoadProduct:
    async def test_successful_load(self, mock_cb):
        mock_cb.get("/api/v1/products").mock(
            return_value=httpx.Response(200, json=[PRODUCT_RECORD])
        )
        mock_cb.post("/api/v1/scene/load").mock(
            return_value=httpx.Response(200, json={"success": True, "node": "Fantasy Sword"})
        )
        result = await daz_load_product("Fantasy Sword")
        assert result["success"] is True
        assert result["product"] == PRODUCT_RECORD

    async def test_search_passes_name_as_q(self, mock_cb):
        captured_params = {}

        def capture_search(request, route):
            captured_params["q"] = request.url.params.get("q")
            return httpx.Response(200, json=[PRODUCT_RECORD])

        mock_cb.get("/api/v1/products").mock(side_effect=capture_search)
        mock_cb.post("/api/v1/scene/load").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        await daz_load_product("Fantasy Sword")
        assert captured_params["q"] == "Fantasy Sword"

    async def test_no_product_found(self, mock_cb):
        mock_cb.get("/api/v1/products").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await daz_load_product("nonexistent item xyz")
        assert result["available"] is True
        assert result["found"] is False

    async def test_unavailable_on_search_connect_error(self, mock_cb):
        mock_cb.get("/api/v1/products").mock(side_effect=httpx.ConnectError("refused"))
        result = await daz_load_product("anything")
        assert result["available"] is False

    async def test_unavailable_on_search_non_200(self, mock_cb):
        mock_cb.get("/api/v1/products").mock(return_value=httpx.Response(500))
        result = await daz_load_product("anything")
        assert result["available"] is False
        assert "500" in result["reason"]

    async def test_unavailable_on_load_connect_error(self, mock_cb):
        mock_cb.get("/api/v1/products").mock(
            return_value=httpx.Response(200, json=[PRODUCT_RECORD])
        )
        mock_cb.post("/api/v1/scene/load").mock(side_effect=httpx.ConnectError("refused"))
        result = await daz_load_product("Fantasy Sword")
        assert result["available"] is False

    async def test_product_without_path_returns_error(self, mock_cb):
        record_no_path = {"sku": "PA-00000", "name": "No Path Product"}
        mock_cb.get("/api/v1/products").mock(
            return_value=httpx.Response(200, json=[record_no_path])
        )
        result = await daz_load_product("No Path Product")
        assert result["available"] is True
        assert result["found"] is True
        assert "error" in result

    async def test_products_dict_wrapper(self, mock_cb):
        """Content browser may wrap results in {products: [...]}."""
        mock_cb.get("/api/v1/products").mock(
            return_value=httpx.Response(200, json={"products": [PRODUCT_RECORD]})
        )
        mock_cb.post("/api/v1/scene/load").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        result = await daz_load_product("Fantasy Sword")
        assert result["success"] is True
