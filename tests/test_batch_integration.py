"""Integration tests — batch operations.

Tools covered
-------------
- daz_batch_set_properties
- daz_batch_transform
- daz_batch_visibility
- daz_batch_select
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_batch_select,
    daz_batch_set_properties,
    daz_batch_transform,
    daz_batch_visibility,
    daz_get_node,
    daz_set_property,
)


# ---------------------------------------------------------------------------
# daz_batch_set_properties
# ---------------------------------------------------------------------------

class TestBatchSetProperties:
    @pytest_asyncio.fixture()
    async def saved_xy(self, live_client, figure_label):
        """Save and restore X/Y translate around test."""
        node = await daz_get_node(figure_label)
        props = node if not node.get("properties") else node["properties"]
        orig_x = float(props.get("XTranslate", 0.0))
        orig_y = float(props.get("YTranslate", 0.0))
        yield orig_x, orig_y
        await daz_set_property(figure_label, "XTranslate", orig_x)
        await daz_set_property(figure_label, "YTranslate", orig_y)

    async def test_set_two_properties(self, live_client, figure_label, saved_xy):
        # Operations use camelCase keys as expected by the DazScript
        result = await daz_batch_set_properties([
            {"nodeLabel": figure_label, "propertyName": "XTranslate", "value": 2.0},
            {"nodeLabel": figure_label, "propertyName": "YTranslate", "value": 0.0},
        ])
        assert isinstance(result, dict)

    async def test_returns_results_list(self, live_client, figure_label, saved_xy):
        result = await daz_batch_set_properties([
            {"nodeLabel": figure_label, "propertyName": "XTranslate", "value": 0.0},
        ])
        assert isinstance(result, dict)
        assert "results" in result or "success" in str(result).lower()

    async def test_empty_list_is_ok(self, live_client):
        result = await daz_batch_set_properties([])
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_batch_transform
# ---------------------------------------------------------------------------

class TestBatchTransform:
    @pytest_asyncio.fixture()
    async def saved_x(self, live_client, figure_label):
        node = await daz_get_node(figure_label)
        props = node if not node.get("properties") else node["properties"]
        orig = float(props.get("XTranslate", 0.0))
        yield orig
        await daz_set_property(figure_label, "XTranslate", orig)

    async def test_translate_single_node(self, live_client, figure_label, saved_x):
        result = await daz_batch_transform(
            node_labels=[figure_label],
            transforms={"XTranslate": 0.0},
        )
        assert isinstance(result, dict)

    async def test_returns_summary(self, live_client, figure_label, saved_x):
        result = await daz_batch_transform(
            node_labels=[figure_label],
            transforms={"XTranslate": 0.0},
        )
        text = str(result)
        assert len(text) > 2  # not empty

    async def test_empty_list_is_ok(self, live_client):
        result = await daz_batch_transform(node_labels=[], transforms={"XTranslate": 0.0})
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_batch_visibility
# ---------------------------------------------------------------------------

class TestBatchVisibility:
    async def test_hide_then_show(self, live_client, figure_label):
        # Hide
        hide_result = await daz_batch_visibility([figure_label], visible=False)
        assert isinstance(hide_result, dict)
        # Show again (teardown)
        show_result = await daz_batch_visibility([figure_label], visible=True)
        assert isinstance(show_result, dict)

    async def test_visible_true_returns_dict(self, live_client, figure_label):
        result = await daz_batch_visibility([figure_label], visible=True)
        assert isinstance(result, dict)

    async def test_empty_list_is_ok(self, live_client):
        result = await daz_batch_visibility([], visible=True)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_batch_select
# ---------------------------------------------------------------------------

class TestBatchSelect:
    async def test_select_figure(self, live_client, figure_label):
        result = await daz_batch_select([figure_label])
        assert isinstance(result, dict)

    async def test_add_to_selection(self, live_client, figure_label):
        result = await daz_batch_select([figure_label], add_to_selection=True)
        assert isinstance(result, dict)

    async def test_empty_list_clears_selection(self, live_client):
        result = await daz_batch_select([])
        assert isinstance(result, dict)
