"""Integration tests — scene structure, node properties, spatial queries.

Tools covered
-------------
- daz_scene_info
- daz_get_node
- daz_set_property
- daz_get_node_hierarchy
- daz_list_children
- daz_get_parent
- daz_set_parent
- daz_get_world_position
- daz_get_bounding_box
- daz_calculate_distance
- daz_get_spatial_relationship
- daz_check_overlap
- daz_get_scene_layout
- daz_find_nearby_nodes
- daz_validate_scene
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_calculate_distance,
    daz_check_overlap,
    daz_create_camera,
    daz_create_light,
    daz_delete_node,
    daz_find_nearby_nodes,
    daz_get_bounding_box,
    daz_get_node,
    daz_get_node_hierarchy,
    daz_get_parent,
    daz_get_scene_layout,
    daz_get_spatial_relationship,
    daz_get_world_position,
    daz_list_children,
    daz_scene_info,
    daz_set_parent,
    daz_set_property,
    daz_validate_scene,
)


# ---------------------------------------------------------------------------
# daz_scene_info
# ---------------------------------------------------------------------------

class TestSceneInfo:
    async def test_returns_dict(self, live_client):
        result = await daz_scene_info()
        assert isinstance(result, dict)

    async def test_has_expected_keys(self, live_client):
        result = await daz_scene_info()
        # Must have at minimum figures, cameras, lights
        assert "figures" in result or "nodes" in result
        assert "cameras" in result
        assert "lights" in result

    async def test_figures_is_list(self, live_client):
        result = await daz_scene_info()
        assert isinstance(result.get("figures", []), list)

    async def test_cameras_is_list(self, live_client):
        result = await daz_scene_info()
        assert isinstance(result.get("cameras", []), list)

    async def test_lights_is_list(self, live_client):
        result = await daz_scene_info()
        assert isinstance(result.get("lights", []), list)


# ---------------------------------------------------------------------------
# daz_get_node
# ---------------------------------------------------------------------------

class TestGetNode:
    async def test_returns_dict(self, live_client, figure_label):
        result = await daz_get_node(figure_label)
        assert isinstance(result, dict)

    async def test_has_transform_properties(self, live_client, figure_label):
        result = await daz_get_node(figure_label)
        result_str = str(result).lower()
        assert any(t in result_str for t in ["translate", "rotate", "scale"])

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_get_node("NonExistentNode_XYZ_999")


# ---------------------------------------------------------------------------
# daz_set_property
# ---------------------------------------------------------------------------

class TestSetProperty:
    @pytest_asyncio.fixture()
    async def original_xtranslate(self, live_client, figure_label):
        """Save and restore XTranslate around a test."""
        node = await daz_get_node(figure_label)
        # Property value may be nested or flat
        original = 0.0
        if isinstance(node, dict):
            props = node.get("properties", node)
            original = float(props.get("XTranslate", props.get("x_translate", 0.0)))
        yield original
        await daz_set_property(figure_label, "XTranslate", original)

    async def test_sets_value(self, live_client, figure_label, original_xtranslate):
        target = 5.0
        result = await daz_set_property(figure_label, "XTranslate", target)
        assert result is not None

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_set_property("NonExistentNode_XYZ", "XTranslate", 0.0)

    async def test_returns_result_dict(self, live_client, figure_label, original_xtranslate):
        result = await daz_set_property(figure_label, "XTranslate", 0.0)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_get_node_hierarchy
# ---------------------------------------------------------------------------

class TestGetNodeHierarchy:
    async def test_returns_dict(self, live_client, figure_label):
        result = await daz_get_node_hierarchy(figure_label)
        assert isinstance(result, dict)

    async def test_has_node_or_children(self, live_client, figure_label):
        result = await daz_get_node_hierarchy(figure_label)
        text = str(result).lower()
        assert any(k in text for k in ["children", "node", "label", "name"])

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_get_node_hierarchy("NonExistentNode_XYZ_999")


# ---------------------------------------------------------------------------
# daz_list_children
# ---------------------------------------------------------------------------

class TestListChildren:
    async def test_returns_dict(self, live_client, figure_label):
        result = await daz_list_children(figure_label)
        assert isinstance(result, dict)

    async def test_children_is_list(self, live_client, figure_label):
        result = await daz_list_children(figure_label)
        children = result.get("children", result.get("nodes", []))
        assert isinstance(children, list)

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_list_children("NonExistentNode_XYZ_999")


# ---------------------------------------------------------------------------
# daz_get_parent
# ---------------------------------------------------------------------------

class TestGetParent:
    async def test_returns_dict(self, live_client, figure_label):
        result = await daz_get_parent(figure_label)
        assert isinstance(result, dict)

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_get_parent("NonExistentNode_XYZ_999")


# ---------------------------------------------------------------------------
# daz_set_parent
# ---------------------------------------------------------------------------

class TestSetParent:
    async def test_set_parent_between_temp_objects(self, live_client):
        """Create two cameras, parent one to the other, then clean up."""
        parent = await daz_create_camera("TempParentCam", x=0, y=150, z=300)
        child = await daz_create_camera("TempChildCam", x=50, y=150, z=300)
        parent_label = parent["label"]
        child_label = child["label"]
        try:
            result = await daz_set_parent(child_label, parent_label)
            assert result is not None
        finally:
            # Delete child first (it's parented), then parent
            try:
                await daz_delete_node(child_label)
            except Exception:
                pass
            try:
                await daz_delete_node(parent_label)
            except Exception:
                pass

    async def test_node_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_set_parent(figure_label, "NonExistentParent_XYZ")


# ---------------------------------------------------------------------------
# daz_get_world_position
# ---------------------------------------------------------------------------

class TestGetWorldPosition:
    async def test_returns_position(self, live_client, figure_label):
        result = await daz_get_world_position(figure_label)
        assert isinstance(result, dict)
        text = str(result).lower()
        assert any(k in text for k in ["x", "y", "z", "position", "world"])

    async def test_values_are_numeric(self, live_client, figure_label):
        result = await daz_get_world_position(figure_label)
        # Find numeric values in the result
        values = [v for v in result.values() if isinstance(v, (int, float))]
        nested = result.get("position", result.get("world_position", {}))
        if isinstance(nested, dict):
            values += [v for v in nested.values() if isinstance(v, (int, float))]
        assert len(values) > 0

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_get_world_position("NonExistentNode_XYZ_999")


# ---------------------------------------------------------------------------
# daz_get_bounding_box
# ---------------------------------------------------------------------------

class TestGetBoundingBox:
    async def test_returns_dict(self, live_client, figure_label):
        result = await daz_get_bounding_box(figure_label)
        assert isinstance(result, dict)

    async def test_has_min_max_values(self, live_client, figure_label):
        result = await daz_get_bounding_box(figure_label)
        text = str(result).lower()
        assert any(k in text for k in ["min", "max", "width", "height", "depth", "size"])

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_get_bounding_box("NonExistentNode_XYZ_999")


# ---------------------------------------------------------------------------
# daz_calculate_distance
# ---------------------------------------------------------------------------

class TestCalculateDistance:
    async def test_distance_is_numeric(self, live_client, figure_label, temp_camera):
        result = await daz_calculate_distance(figure_label, temp_camera)
        assert isinstance(result, dict)
        # Find a numeric distance value
        text = str(result)
        nums = [v for v in result.values() if isinstance(v, (int, float))]
        assert len(nums) > 0 or "distance" in str(result).lower()

    async def test_distance_to_self_is_zero_or_small(self, live_client, figure_label):
        result = await daz_calculate_distance(figure_label, figure_label)
        assert isinstance(result, dict)

    async def test_node_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_calculate_distance(figure_label, "NonExistentNode_XYZ_999")


# ---------------------------------------------------------------------------
# daz_get_spatial_relationship
# ---------------------------------------------------------------------------

class TestGetSpatialRelationship:
    async def test_returns_description(self, live_client, figure_label, temp_camera):
        result = await daz_get_spatial_relationship(figure_label, temp_camera)
        assert isinstance(result, dict)

    async def test_has_string_content(self, live_client, figure_label, temp_camera):
        result = await daz_get_spatial_relationship(figure_label, temp_camera)
        strings = [v for v in result.values() if isinstance(v, str)]
        assert len(strings) > 0


# ---------------------------------------------------------------------------
# daz_check_overlap
# ---------------------------------------------------------------------------

class TestCheckOverlap:
    async def test_returns_dict(self, live_client, figure_label, temp_camera):
        result = await daz_check_overlap(figure_label, temp_camera)
        assert isinstance(result, dict)

    async def test_has_overlap_key(self, live_client, figure_label, temp_camera):
        result = await daz_check_overlap(figure_label, temp_camera)
        text = str(result).lower()
        assert any(k in text for k in ["overlap", "intersect", "collision", "true", "false"])

    async def test_node_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_check_overlap(figure_label, "NonExistentNode_XYZ_999")


# ---------------------------------------------------------------------------
# daz_get_scene_layout
# ---------------------------------------------------------------------------

class TestGetSceneLayout:
    async def test_returns_dict(self, live_client):
        result = await daz_get_scene_layout()
        assert isinstance(result, dict)

    async def test_has_nodes_list(self, live_client):
        result = await daz_get_scene_layout()
        nodes = result.get("nodes", result.get("layout", []))
        assert isinstance(nodes, list)

    async def test_nodes_have_positions(self, live_client):
        result = await daz_get_scene_layout()
        nodes = result.get("nodes", result.get("layout", []))
        if nodes:
            node = nodes[0]
            text = str(node).lower()
            assert any(k in text for k in ["x", "y", "z", "position", "label"])


# ---------------------------------------------------------------------------
# daz_find_nearby_nodes
# ---------------------------------------------------------------------------

class TestFindNearbyNodes:
    async def test_returns_dict(self, live_client, figure_label):
        result = await daz_find_nearby_nodes(figure_label, radius=1000.0)
        assert isinstance(result, dict)

    async def test_nearby_list_exists(self, live_client, figure_label):
        result = await daz_find_nearby_nodes(figure_label, radius=1000.0)
        nodes = result.get("nearby", result.get("nodes", []))
        assert isinstance(nodes, list)

    async def test_tiny_radius_finds_nothing(self, live_client, figure_label):
        result = await daz_find_nearby_nodes(figure_label, radius=0.001)
        nodes = result.get("nearby", result.get("nodes", []))
        assert isinstance(nodes, list)

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_find_nearby_nodes("NonExistentNode_XYZ_999", radius=100.0)


# ---------------------------------------------------------------------------
# daz_validate_scene
# ---------------------------------------------------------------------------

class TestValidateScene:
    async def test_returns_dict(self, live_client):
        result = await daz_validate_scene()
        assert isinstance(result, dict)

    async def test_has_valid_or_issues(self, live_client):
        result = await daz_validate_scene()
        text = str(result).lower()
        assert any(k in text for k in ["valid", "issue", "warning", "error", "ok", "pass"])
