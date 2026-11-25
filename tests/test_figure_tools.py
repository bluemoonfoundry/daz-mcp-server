"""Unit tests (no Studio) for look-at, reach and reset-pose on dazpy
(daz-mcp-server-dnj)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from dazpy import BoneAim, LookAtResult
from dazpy.exceptions import NodeNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import figure

G9 = ["hip", "spine1", "spine2", "spine3", "spine4", "neck1", "neck2", "head",
      "l_eye", "r_eye", "r_upperarm", "r_forearm", "r_hand"]
G8 = ["hip", "abdomenLower", "chestLower", "chestUpper", "neckLower", "neckUpper", "head",
      "lEye", "rEye"]


class FakeSkel:
    def __init__(self, label, bones, head=(0.0, 150.0, 0.0)):
        self.label = label
        self.bones = bones
        self.head = head
        self.look_calls = []
        self.rotations = None
        self.reach_calls = []
        self.position = None
        self.props = {}

    def describe(self):
        return SimpleNamespace(label=self.label)

    def bone_names(self):
        return list(self.bones)

    def look_at(self, point, chain):
        self.look_calls.append((tuple(point), list(chain)))
        return LookAtResult([BoneAim(b, -1.0, 2.0) for b, _ in chain], [])

    def find_bone(self, name):
        x, y, z = self.head
        return SimpleNamespace(position={"x": x, "y": y, "z": z})

    def hand_to_target(self, point, *, source_anchor, max_iterations):
        assert max_iterations == 40
        self.reach_calls.append((tuple(point), source_anchor))
        return SimpleNamespace(converged=True, final_error=0.4, iterations=5,
                               chain=["r_upperarm", "r_forearm", "r_hand"])

    def set_bone_rotations(self, data):
        self.rotations = dict(data)

    def set_position(self, x, y, z):
        self.position = (x, y, z)

    def set_numeric_property(self, name, value, **_):
        self.props[name] = value


class FakeScene:
    def __init__(self):
        self.nodes = {"Genesis 9": FakeSkel("Genesis 9", G9),
                      "Genesis 8 Female": FakeSkel("Genesis 8 Female", G8,
                                                   head=(0.0, 160.0, 100.0))}

    def resolve_node(self, ref):
        if ref not in self.nodes:
            raise NodeNotFoundError(f"Node not found: {ref!r}")
        return self.nodes[ref]

    def find_skeleton_by_label(self, ref):
        return self.resolve_node(ref)

    def find_node_by_label(self, ref):
        return self.resolve_node(ref)


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(figure, "get_scene", lambda: s)
    from daz_mcp_server.tools import morph
    monkeypatch.setattr(morph, "get_scene", lambda: s)
    return s


async def test_look_at_point_head_mode_g9(scene):
    r = await figure.daz_look_at_point("Genesis 9", 0, 160, 200)
    point, chain = scene.nodes["Genesis 9"].look_calls[0]
    assert point == (0, 160, 200)
    assert chain == [("head", 0.6), ("l_eye", 1.0), ("r_eye", 1.0)]
    assert r["success"] is True and r["rotatedBones"] == ["head", "l_eye", "r_eye"]
    assert r["rotations"][0] == {"bone": "head", "x": -1.0, "y": 2.0}


async def test_look_at_point_full_mode_g8_names(scene):
    await figure.daz_look_at_point("Genesis 8 Female", 0, 160, 200, mode="full")
    chain = [b for b, _ in scene.nodes["Genesis 8 Female"].look_calls[0][1]]
    assert chain == ["hip", "chestLower", "chestUpper", "neckLower", "neckUpper", "head",
                     "lEye", "rEye"]


async def test_look_at_point_bad_mode(scene):
    with pytest.raises(ToolError, match="mode"):
        await figure.daz_look_at_point("Genesis 9", 0, 0, 0, mode="spine")


async def test_look_at_character_aims_at_target_head(scene):
    r = await figure.daz_look_at_character("Genesis 9", "Genesis 8 Female", mode="eyes")
    point, chain = scene.nodes["Genesis 9"].look_calls[0]
    assert point == (0.0, 160.0, 100.0)
    assert [b for b, _ in chain] == ["l_eye", "r_eye"]
    assert r["targetPosition"] == {"x": 0.0, "y": 160.0, "z": 100.0}
    assert r["source"] == "Genesis 9" and r["target"] == "Genesis 8 Female"


async def test_reach_toward_uses_hand_solver(scene):
    r = await figure.daz_reach_toward("Genesis 9", "right", 50, 130, 80)
    assert scene.nodes["Genesis 9"].reach_calls == [((50, 130, 80), "r_hand")]
    assert r["converged"] is True and r["finalError"] == 0.4
    assert r["bones"] == ["r_upperarm", "r_forearm", "r_hand"]


async def test_reach_toward_bad_side(scene):
    with pytest.raises(ToolError, match="side"):
        await figure.daz_reach_toward("Genesis 9", "middle", 0, 0, 0)


async def test_reset_pose(scene):
    r = await figure.daz_reset_pose("Genesis 9", zero_transforms=True)
    skel = scene.nodes["Genesis 9"]
    assert skel.rotations == {b: (0.0, 0.0, 0.0) for b in G9}
    assert skel.position == (0.0, 0.0, 0.0) and skel.props == {"Scale": 1.0}
    assert r == {"node": "Genesis 9", "bones_reset": len(G9), "transforms_zeroed": True}


async def test_reset_pose_missing(scene):
    with pytest.raises(ToolError, match="Node not found"):
        await figure.daz_reset_pose("Ghost")
