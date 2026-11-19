"""Unit tests (no Studio) for daz_batch_select replace semantics and the
spatial tools' include_types filter (daz-mcp-server-i2l, -skr)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from dazpy.exceptions import NodeNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import spatial, transform

# --------------------------------------------------------------------------
# daz_batch_select
# --------------------------------------------------------------------------


class SelectScene:
    def __init__(self, labels):
        self.selected = {"Old Selection"}
        self.known = set(labels)
        self.calls = []

    def select_all(self, on=True):
        self.calls.append(("select_all", on))
        if not on:
            self.selected.clear()

    def find_node_by_label(self, label):
        if label not in self.known:
            raise NodeNotFoundError(label)
        scene = self
        return SimpleNamespace(select=lambda on=True: scene.selected.add(label))


@pytest.fixture()
def select_scene(monkeypatch):
    scene = SelectScene(["A", "B"])
    monkeypatch.setattr(transform, "get_scene", lambda: scene)
    return scene


async def test_batch_select_replaces_selection_by_default(select_scene):
    result = await transform.daz_batch_select(["A", "Missing"])
    assert select_scene.selected == {"A"}
    assert select_scene.calls == [("select_all", False)]
    assert result == {"selected": ["A"], "count": 1, "total": 2}


async def test_batch_select_add_keeps_prior_selection(select_scene):
    await transform.daz_batch_select(["B"], add_to_selection=True)
    assert select_scene.selected == {"Old Selection", "B"}
    assert select_scene.calls == []


# --------------------------------------------------------------------------
# include_types
# --------------------------------------------------------------------------

TRANSFORMS = [
    {"label": "Genesis 9", "type": "figures", "position": [0, 0, 0]},
    {"label": "Shirt", "type": "wearables", "position": [0, 0, 0]},
    {"label": "hip", "type": "bones", "position": [0, 100, 0]},
    {"label": "Camera 1", "type": "cameras", "position": [0, 150, 50]},
    {"label": "Spot Light 1", "type": "lights", "position": [500, 0, 0]},
    {"label": "Chair", "type": "props", "position": [30, 0, 0]},
]


@pytest.fixture()
def typed_scene(monkeypatch):
    client = SimpleNamespace(scripts=[])

    def execute(script):
        client.scripts.append(script)
        return SimpleNamespace(value=[dict(t) for t in TRANSFORMS])

    client.execute = execute
    monkeypatch.setattr(spatial, "get_daz_client", lambda: client)
    chair = SimpleNamespace(position={"x": 30, "y": 0, "z": 0})
    monkeypatch.setattr(
        spatial, "get_scene",
        lambda: SimpleNamespace(find_node_by_label=lambda label: chair),
    )
    return client


async def test_scene_layout_unfiltered_returns_all_with_types(typed_scene):
    result = await spatial.daz_get_scene_layout()
    assert result["count"] == len(TRANSFORMS)
    assert [n["type"] for n in result["nodes"]] == [t["type"] for t in TRANSFORMS]
    assert "DzSkeleton" in typed_scene.scripts[0]


async def test_scene_layout_filters_by_type(typed_scene):
    result = await spatial.daz_get_scene_layout(["figures", "Cameras"])
    assert [n["label"] for n in result["nodes"]] == ["Genesis 9", "Camera 1"]


async def test_find_nearby_filters_by_type(typed_scene):
    result = await spatial.daz_find_nearby_nodes(
        "Chair", radius=80, include_types=["figures"]
    )
    assert [n["label"] for n in result["nearby_nodes"]] == ["Genesis 9"]
    assert result["nearby_nodes"][0]["type"] == "figures"


async def test_find_nearby_unfiltered_keeps_everything_in_radius(typed_scene):
    result = await spatial.daz_find_nearby_nodes("Chair", radius=80)
    labels = {n["label"] for n in result["nearby_nodes"]}
    assert labels == {"Genesis 9", "Shirt"}  # hip/camera > 80 cm, light 470 cm


@pytest.mark.parametrize("tool", ["layout", "nearby"])
async def test_unknown_type_is_rejected(typed_scene, tool):
    with pytest.raises(ToolError, match="Unknown include_types"):
        if tool == "layout":
            await spatial.daz_get_scene_layout(["characters"])
        else:
            await spatial.daz_find_nearby_nodes("Chair", include_types=["chars"])
    assert not typed_scene.scripts
