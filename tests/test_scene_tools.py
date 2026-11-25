"""Unit tests (no Studio) for the scene tools on dazpy: daz_scene_info,
daz_load_file (replace), daz_get_node_hierarchy and the checkpoint tools
(daz-mcp-server-14w)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from dazpy.exceptions import NodeNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import scene as scene_tools
from daz_mcp_server.tools import utility

OVERVIEW = {
    "scene_file": "C:/scenes/test.duf", "selected_node": "Genesis 9",
    "figures": [{"name": "Genesis9", "label": "Genesis 9", "type": "DzFigure"}],
    "cameras": [{"name": "Camera", "label": "Camera"}],
    "lights": [], "total_nodes": 140,
}


class FakeState:
    captured = 0

    def __init__(self):
        self.skeleton_poses = {"Genesis9": object(), "Genesis9Eyes": object()}
        self.camera_transforms = {"Camera": {}}
        self.light_transforms = {}

    @classmethod
    def capture(cls, scene):
        cls.captured += 1
        return cls()

    def apply(self, scene):
        return {"restored": ["Genesis9", "Camera"], "skipped": [], "errors": [],
                "complete": True, "backup": None}


class FakeScene:
    def __init__(self):
        self.loads = []
        self.hier_calls = []

    def overview(self):
        return dict(OVERVIEW)

    def load(self, path, *, replace=False):
        self.loads.append((path, replace))

    def resolve_node(self, ref):
        if ref != "Genesis 9":
            raise NodeNotFoundError(f"Node not found: {ref!r}")
        calls = self.hier_calls

        def hierarchy(max_depth=None):
            calls.append(max_depth)
            return {"node": "Genesis 9", "total_descendants": 1,
                    "hierarchy": {"label": "Genesis 9", "name": "Genesis9", "type": "DzFigure",
                                  "element_id": 5,
                                  "children": [{"label": "Hip", "name": "hip", "type": "DzBone",
                                                "element_id": 6}]}}
        return SimpleNamespace(hierarchy=hierarchy)


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(scene_tools, "get_scene", lambda: s)
    monkeypatch.setattr(scene_tools, "DazSceneState", FakeState)
    monkeypatch.setattr(scene_tools, "_CHECKPOINTS", {})
    return s


async def test_scene_info_keeps_camel_case_shape(scene):
    r = await scene_tools.daz_scene_info()
    assert r == {"sceneFile": "C:/scenes/test.duf", "selectedNode": "Genesis 9",
                 "figures": OVERVIEW["figures"], "cameras": OVERVIEW["cameras"],
                 "lights": [], "totalNodes": 140}


async def test_suggest_next_action_reads_scene_info(scene):
    r = await utility.daz_suggest_next_action()
    actions = [s["action"] for s in r["suggestions"]]
    assert "daz_create_light" in actions and "daz_load_file" not in actions


async def test_load_file_replace(scene):
    r = await scene_tools.daz_load_file("C:/scenes/a.duf", merge=False)
    assert scene.loads == [("C:/scenes/a.duf", True)]
    assert r == {"success": True, "file": "C:/scenes/a.duf"}


async def test_hierarchy_default_depth_and_element_ids(scene):
    r = await scene_tools.daz_get_node_hierarchy("Genesis 9")
    assert scene.hier_calls == [10]
    assert r["totalDescendants"] == 1
    assert r["hierarchy"]["elementID"] == 5
    assert r["hierarchy"]["children"][0] == {"label": "Hip", "name": "hip", "type": "DzBone",
                                             "elementID": 6}


async def test_hierarchy_zero_is_unlimited(scene):
    await scene_tools.daz_get_node_hierarchy("Genesis 9", max_depth=0)
    assert scene.hier_calls == [0]


async def test_hierarchy_requires_node(scene):
    with pytest.raises(ToolError, match="node_label"):
        await scene_tools.daz_get_node_hierarchy()


async def test_checkpoint_round_trip(scene):
    saved = await scene_tools.daz_save_scene_state("before")
    assert saved["checkpoint_name"] == "before" and saved["node_count"] == 3
    listed = await scene_tools.daz_list_checkpoints()
    assert listed["count"] == 1 and listed["checkpoints"][0]["node_count"] == 3
    restored = await scene_tools.daz_restore_scene_state("before")
    assert restored["checkpoint_name"] == "before"
    assert restored["restored"] == ["Genesis9", "Camera"] and restored["complete"] is True


async def test_restore_unknown_checkpoint(scene):
    with pytest.raises(ToolError, match="not found"):
        await scene_tools.daz_restore_scene_state("nope")
