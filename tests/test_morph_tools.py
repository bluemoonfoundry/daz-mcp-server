"""Unit tests (no Studio) for daz_set_emotion, daz_set_body_language and
daz_direct_gaze on dazpy primitives (daz-mcp-server-96d, -3oq, -7w8, -w88).

The fake skeletons carry the bone and dial names verified live on stock
Genesis 9 and Genesis 8 Female (DS 4.24, 2026-11-24).
"""
from __future__ import annotations

import math
from types import SimpleNamespace

import pytest
from dazpy import NumericCandidateMatch, ViewportCamera
from dazpy.exceptions import NodeNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import morph

G9_BONES = ["hip", "spine1", "spine2", "spine3", "spine4", "neck1", "neck2", "head",
            "l_shoulder", "l_upperarm", "r_shoulder", "r_upperarm"]
G8_BONES = ["hip", "abdomenLower", "abdomenUpper", "chestLower", "chestUpper",
            "neckLower", "neckUpper", "head", "lShldrBend", "lShldrTwist",
            "rShldrBend", "rShldrTwist"]
G9_DIALS = {"facs_ctrl_Happy": 0.0, "facs_ctrl_Sad": 0.4, "facs_ctrl_Angry": 0.0,
            "Smile": 0.0, "facs_ctrl_EyeSquint": 0.0}


class FakeSkeleton:
    def __init__(self, bones, dials=None, head_pos=(0.0, 150.0, 0.0)):
        self.bones = list(bones)
        self.dials = dict(dials or {})
        self.axes: dict[str, dict[str, float]] = {}
        self.slot_calls: list[list] = []
        self.head_pos = head_pos
        self.x_limit = 1000.0

    def bone_names(self):
        return list(self.bones)

    def set_bone_axes(self, data):
        missing = []
        for bone, axes in data.items():
            if bone not in self.bones:
                missing.append(bone)
                continue
            self.axes.setdefault(bone, {}).update(axes)
        return missing

    def set_numeric_candidates(self, slots):
        self.slot_calls.append([(tuple(n), v) for n, v in slots])
        out = []
        for names, value in slots:
            hit = next((n for n in names if n in self.dials), None)
            if hit is not None:
                self.dials[hit] = value
            out.append(NumericCandidateMatch(tuple(names), float(value), hit,
                                             "property" if hit else None,
                                             value if hit else None))
        return out

    def find_bone(self, name):
        if name not in self.bones:
            raise NodeNotFoundError(name)
        x, y, z = self.head_pos
        axes = self.axes.get(name, {})
        euler = tuple(min(axes.get(a, 0.0), self.x_limit) if a == "x" else axes.get(a, 0.0)
                      for a in "xyz")
        return SimpleNamespace(position={"x": x, "y": y, "z": z}, local_euler=euler)


class FakeScene:
    def __init__(self, skeletons, nodes=None, camera=None):
        self.skeletons = skeletons
        self.nodes = nodes or {}
        self.camera = camera

    def find_skeleton_by_label(self, label):
        if label not in self.skeletons:
            raise NodeNotFoundError(f"Skeleton with label not found: {label!r}")
        return self.skeletons[label]

    def find_node_by_label(self, label):
        if label not in self.nodes:
            raise NodeNotFoundError(label)
        x, y, z = self.nodes[label]
        return SimpleNamespace(position={"x": x, "y": y, "z": z})

    def viewport_camera(self):
        return self.camera


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene({
        "Genesis 9": FakeSkeleton(G9_BONES, G9_DIALS),
        "Genesis 8 Female": FakeSkeleton(G8_BONES),
        "Bare": FakeSkeleton(G9_BONES, {"Smile": 0.0, "facs_ctrl_EyeSquint": 0.0}),
    })
    monkeypatch.setattr(morph, "get_scene", lambda: s)
    return s


# --------------------------------------------------------------------------
# daz_set_emotion
# --------------------------------------------------------------------------


async def test_emotion_uses_full_face_controller_and_clears_other_faces(scene):
    g9 = scene.skeletons["Genesis 9"]
    result = await morph.daz_set_emotion("Genesis 9", "happy", 0.5)
    assert result["applied_morphs"] == [{"morph": "facs_ctrl_Happy", "value": 0.5}]
    assert g9.dials["facs_ctrl_Happy"] == 0.5
    assert g9.dials["facs_ctrl_Sad"] == 0.0  # previous emotion's face cleared
    assert len(g9.slot_calls) == 1  # feature slots not needed
    assert result["not_found"] == []


async def test_emotion_body_adjustment_reaches_genesis9_spine(scene):
    # 'chestUpper' never matched before (onf): it is spine4 on Genesis 9.
    g9 = scene.skeletons["Genesis 9"]
    result = await morph.daz_set_emotion("Genesis 9", "happy", 0.5)
    assert g9.axes == {"spine4": {"x": pytest.approx(1.5)}}
    assert result["body_adjustments"] == [
        {"bone": "spine4", "property": "XRotate", "value": pytest.approx(1.5)}]


async def test_emotion_falls_back_to_feature_dials(scene):
    bare = scene.skeletons["Bare"]
    result = await morph.daz_set_emotion("Bare", "loving", 1.0)
    applied = {m["morph"]: m["value"] for m in result["applied_morphs"]}
    assert applied == {"Smile": 0.6, "facs_ctrl_EyeSquint": 0.35}
    assert len(bare.slot_calls) == 2


async def test_emotion_reports_unresolved_feature_slots(scene):
    result = await morph.daz_set_emotion("Genesis 8 Female", "shy", 0.5)
    assert result["applied_morphs"] == []
    assert result["not_found"] and all(isinstance(n, str) for n in result["not_found"])


async def test_neutral_clears_faces_without_body(scene):
    g9 = scene.skeletons["Genesis 9"]
    result = await morph.daz_set_emotion("Genesis 9", "neutral")
    assert g9.dials["facs_ctrl_Sad"] == 0.0
    assert result["applied_morphs"] == [] and result["body_adjustments"] == []


async def test_emotion_unknown_figure_is_tool_error(scene):
    with pytest.raises(ToolError, match="Nobody"):
        await morph.daz_set_emotion("Nobody", "happy")


async def test_emotion_validates_inputs(scene):
    with pytest.raises(ToolError, match="Unknown emotion"):
        await morph.daz_set_emotion("Genesis 9", "smug")
    with pytest.raises(ToolError, match="intensity"):
        await morph.daz_set_emotion("Genesis 9", "happy", 1.5)


# --------------------------------------------------------------------------
# daz_set_body_language
# --------------------------------------------------------------------------


async def test_body_language_genesis8_names(scene):
    g8 = scene.skeletons["Genesis 8 Female"]
    result = await morph.daz_set_body_language("Genesis 8 Female", "confident")
    assert g8.axes == {"chestUpper": {"x": 5.0}, "lShldrBend": {"z": -5.0},
                       "rShldrBend": {"z": 5.0}}
    assert result["success"] is True and result["not_found"] == []


async def test_body_language_genesis9_names_scaled(scene):
    g9 = scene.skeletons["Genesis 9"]
    await morph.daz_set_body_language("Genesis 9", "relaxed", 0.5)
    assert g9.axes == {"spine4": {"x": -1.5}, "l_upperarm": {"z": 2.0},
                       "r_upperarm": {"z": -2.0}, "neck1": {"x": 1.0}}


async def test_body_language_reports_missing_bones(monkeypatch):
    s = FakeScene({"Prop Rig": FakeSkeleton(["hip", "chestUpper"])})
    monkeypatch.setattr(morph, "get_scene", lambda: s)
    result = await morph.daz_set_body_language("Prop Rig", "confident")
    assert [a["bone"] for a in result["applied"]] == ["chestUpper"]
    assert result["not_found"] == ["lShldr", "rShldr"]


async def test_body_language_validates_posture(scene):
    with pytest.raises(ToolError, match="Unknown posture"):
        await morph.daz_set_body_language("Genesis 9", "slouchy")


# --------------------------------------------------------------------------
# daz_direct_gaze
# --------------------------------------------------------------------------


async def test_gaze_fixed_direction_writes_only_x_and_y(scene):
    g9 = scene.skeletons["Genesis 9"]
    result = await morph.daz_direct_gaze("Genesis 9", "up")
    assert g9.axes == {"head": {"x": -25.0, "y": 0.0}}
    assert result["success"] is True


async def test_gaze_neck_fallback_on_genesis9_without_head(monkeypatch):
    skel = FakeSkeleton([b for b in G9_BONES if b != "head"])
    monkeypatch.setattr(morph, "get_scene", lambda: FakeScene({"G": skel}))
    await morph.daz_direct_gaze("G", "left")
    assert skel.axes == {"neck2": {"x": 0.0, "y": -35.0}}


async def test_gaze_camera_uses_viewport_camera(scene):
    # Camera straight ahead (+Z) at head height: no rotation.
    scene.camera = ViewportCamera("Perspective View", "PerspectiveView", False,
                                  (0.0, 150.0, 300.0))
    await morph.daz_direct_gaze("Genesis 9", "camera")
    head = scene.skeletons["Genesis 9"].axes["head"]
    assert head["x"] == pytest.approx(0.0) and head["y"] == pytest.approx(0.0)


async def test_gaze_camera_above_and_to_the_side(scene):
    scene.camera = ViewportCamera("Camera 1", "Camera 1", True, (100.0, 250.0, 0.0))
    await morph.daz_direct_gaze("Genesis 9", "camera")
    head = scene.skeletons["Genesis 9"].axes["head"]
    assert head["y"] == pytest.approx(90.0)
    assert head["x"] == pytest.approx(-math.degrees(math.atan2(100, 100)) * 0.5)


async def test_gaze_camera_without_viewport_is_tool_error(scene):
    scene.camera = None
    with pytest.raises(ToolError, match="viewport camera"):
        await morph.daz_direct_gaze("Genesis 9", "camera")


async def test_gaze_character_non_figure_target_uses_node_origin(scene):
    scene.nodes["Lamp"] = (0.0, 150.0, -200.0)
    result = await morph.daz_direct_gaze("Genesis 9", "character", "Lamp")
    head = scene.skeletons["Genesis 9"].axes["head"]
    assert head["y"] == pytest.approx(180.0)
    assert result["direction"] == "character"


async def test_gaze_character_aims_at_target_figure_head(scene):
    # Target is a figure: aim at its head bone, not its root (feet).
    scene.skeletons["Genesis 8 Female"].head_pos = (0.0, 150.0, 100.0)
    scene.nodes["Genesis 8 Female"] = (0.0, 0.0, 100.0)
    await morph.daz_direct_gaze("Genesis 9", "character", "Genesis 8 Female")
    head = scene.skeletons["Genesis 9"].axes["head"]
    assert head["x"] == pytest.approx(0.0) and head["y"] == pytest.approx(0.0)


async def test_gaze_reports_read_back_rotation(scene):
    g9 = scene.skeletons["Genesis 9"]
    g9.x_limit = 10.0  # Studio clamps the head's pitch
    result = await morph.daz_direct_gaze("Genesis 9", "down")
    assert result["applied"][0] == {"bone": "head", "property": "XRotate", "value": 10.0}
    assert result["requested"] == {"x": 20.0, "y": 0.0}


async def test_gaze_missing_target_is_tool_error(scene):
    with pytest.raises(ToolError, match="Ghost"):
        await morph.daz_direct_gaze("Genesis 9", "character", "Ghost")
