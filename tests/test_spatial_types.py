"""Mock tests for include_types filtering in spatial tools."""
from unittest.mock import MagicMock

import pytest
from fastmcp.exceptions import ToolError

from vangard_daz_mcp import _client
from vangard_daz_mcp.tools.spatial import daz_find_nearby_nodes, daz_get_scene_layout

TRANSFORMS = [
    {"name": "Genesis9", "label": "Hero", "position": [0, 0, 0], "rotation": [0, 0, 0]},
    {"name": "Cam1", "label": "Cam", "position": [10, 0, 0], "rotation": [0, 0, 0]},
    {"name": "Key", "label": "Key", "position": [0, 0, 20], "rotation": [0, 0, 0]},
    {"name": "Chair", "label": "Chair", "position": [-30, 0, 0], "rotation": [0, 0, 0]},
]
TYPES = [
    {"name": n["name"], "label": n["label"], "type": ty}
    for n, ty in zip(TRANSFORMS, ["figures", "cameras", "lights", "props"])
]


@pytest.fixture(autouse=True)
def fake_scene(monkeypatch):
    scene = MagicMock()
    scene.all_node_transforms.return_value = TRANSFORMS
    scene.find_node_by_label.return_value.position = {"x": 0, "y": 0, "z": 0}
    client = MagicMock()
    client.execute.return_value.value = TYPES
    _client.set_scene(scene)
    monkeypatch.setattr("vangard_daz_mcp.tools.spatial.get_daz_client", lambda: client)
    yield
    _client.set_scene(None)


async def test_layout_filters_by_type():
    r = await daz_get_scene_layout(["figures", "cameras"])
    assert {n["label"] for n in r["nodes"]} == {"Hero", "Cam"}
    assert {n["type"] for n in r["nodes"]} == {"figures", "cameras"}


async def test_layout_unfiltered_has_types():
    r = await daz_get_scene_layout()
    assert r["count"] == 4 and all("type" in n for n in r["nodes"])


async def test_nearby_filters_by_type():
    r = await daz_find_nearby_nodes("Hero", radius=100, include_types=["props"])
    assert [n["label"] for n in r["nearby_nodes"]] == ["Chair"]


async def test_invalid_type_rejected():
    with pytest.raises(Exception, match="Invalid include_types"):
        await daz_get_scene_layout(["bogus"])
