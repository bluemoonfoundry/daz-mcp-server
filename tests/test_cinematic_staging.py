"""Unit tests (no Studio) for daz_arrange_characters / daz_create_character_path
on dazpy (daz-mcp-server-ord, staging slice)."""
from __future__ import annotations

import pytest
from dazpy import BatchPropertyResult, NodeInfo, NumericCandidateMatch, ViewportCamera
from dazpy.exceptions import NodeNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server import _cinematic_staging as st
from daz_mcp_server.tools import cinematic


class FakeNode:
    def __init__(self, label, eid):
        self.label, self.eid, self.keys = label, eid, {}

    def describe(self):
        return NodeInfo(self.label, self.label, "DzFigure", self.eid, None, 0)

    def key_numeric_candidates(self, slots):
        out = []
        for names, keys in slots:
            self.keys[names[0]] = list(keys)
            out.append(NumericCandidateMatch(tuple(names), 0.0, names[0], "property", None))
        return out


class FakeScene:
    def __init__(self):
        self.nodes = {"A": FakeNode("A", 1), "B": FakeNode("B", 2), "C": FakeNode("C", 3)}
        self.batches = []
        self.camera = ViewportCamera("Perspective View", "PerspectiveView", False,
                                     (0.0, 150.0, 500.0))

    def resolve_node(self, ref):
        if ref not in self.nodes:
            raise NodeNotFoundError(f"Node not found: {ref!r}")
        return self.nodes[ref]

    def viewport_camera(self):
        return self.camera

    def set_numeric_properties(self, ops):
        self.batches.append(list(ops))
        return [BatchPropertyResult(True, n, p, v) for n, p, v in ops]


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(st, "get_scene", lambda: s)
    return s


def test_formations():
    c = {"x": 0, "y": 0, "z": 0}
    assert [p["x"] for p in st.formation("line", 3, 80, c)] == [-80, 0, 80]
    tri = st.formation("triangle", 4, 100, c)
    assert [(p["x"], p["z"]) for p in tri] == [(-50, -60), (50, -60), (-50, 30), (50, 30)]
    circ = st.formation("conversation-circle", 4, 100, c)
    assert circ[1]["x"] == pytest.approx(100) and circ[2]["z"] == pytest.approx(-100)


async def test_arrange_facing_center_one_batch(scene):
    r = await cinematic.daz_arrange_characters(["A", "B"], "line", 100, "center")
    assert len(scene.batches) == 1 and len(scene.batches[0]) == 8
    assert r["characters"][0] == {"label": "A", "position": {"x": -50.0, "y": 0.0, "z": 0.0},
                                  "rotation": 90.0}
    assert r["characters"][1]["rotation"] == -90.0


async def test_arrange_facing_camera(scene):
    r = await cinematic.daz_arrange_characters(["A"], "line", 100, "camera")
    assert r["characters"][0]["rotation"] == 0.0
    scene.camera = ViewportCamera("Cam", "Cam", True, (500.0, 150.0, 0.0))
    r = await cinematic.daz_arrange_characters(["A"], "line", 100, "camera")
    assert r["characters"][0]["rotation"] == 90.0


async def test_character_path_keys_frames(scene):
    r = await cinematic.daz_create_character_path("A", [
        {"frame": 30, "position": {"x": 100, "y": 0, "z": 0}},
        {"frame": 0, "position": {"x": 0, "y": 0, "z": 0}}])
    keys = scene.nodes["A"].keys
    assert keys["XTranslate"] == [(0, 0.0), (30, 100.0)]
    assert keys["YRotate"] == [(0, 90.0)]
    assert r["keyframesSet"] == 7 and r["totalDistance"] == 100.0


async def test_path_missing_character(scene):
    with pytest.raises(ToolError, match="Node not found"):
        await cinematic.daz_create_character_path("Z", [
            {"frame": 0, "position": {"x": 0, "y": 0, "z": 0}},
            {"frame": 9, "position": {"x": 1, "y": 0, "z": 0}}])


class ConvSkel(FakeNode):
    def __init__(self, label, eid, bones, dials):
        super().__init__(label, eid)
        self.bones, self.dials, self.bone_keys, self.keyed = bones, set(dials), {}, []
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}

    def bone_names(self):
        return list(self.bones)

    def key_numeric_candidates(self, slots):
        out = []
        for names, keys in slots:
            hit = next((n for n in names if n in self.dials), None)
            if hit:
                self.keyed.append((hit, list(keys)))
            out.append(NumericCandidateMatch(tuple(names), 0.0, hit, "property" if hit else None,
                                             None))
        return out

    def look_at(self, point, chain):
        from dazpy import BoneAim, LookAtResult
        return LookAtResult([BoneAim(b, -2.0, 30.0) for b, _ in chain], [])

    def key_bone_axes(self, data):
        self.bone_keys.update(data)
        return []

    def find_bone(self, name):
        from types import SimpleNamespace
        return SimpleNamespace(position={"x": 100.0, "y": 150.0, "z": 0.0})


async def test_conversation_keys_speaker_face_and_listener_look(scene):
    scene.nodes["A"] = ConvSkel("A", 1, ["neck1", "head"], ["facs_ctrl_Happy"])
    scene.nodes["B"] = ConvSkel("B", 2, ["neckLower", "head"], ["eCTRLHappy_HD"])
    scene.find_skeleton_by_label = lambda label: scene.nodes[label]
    r = await cinematic.daz_animate_conversation("A", "B", [
        {"speaker": "A", "startFrame": 10, "endFrame": 40, "emotion": "happy",
         "intensity": 0.5}])
    assert scene.nodes["A"].keyed == [("facs_ctrl_Happy", [(10, 0.5)])]
    assert scene.nodes["B"].bone_keys == {
        "neckLower": {"x": [(10, -2.0), (40, -2.0)], "y": [(10, 30.0), (40, 30.0)]},
        "head": {"x": [(10, -2.0), (40, -2.0)], "y": [(10, 30.0), (40, 30.0)]}}
    assert r["beatsApplied"][0]["actions"] == ["Applied happy emotion (1 morphs)",
                                               "Listener looks at speaker"]


async def test_choreograph_faces_pair_at_action_spacing(scene):
    r = await cinematic.daz_choreograph_action("fight", ["A", "B"])
    assert r["positions"][0] == {"character": "A", "position": {"x": -50.0, "y": 0.0, "z": 0.0},
                                 "rotation": 90.0}
    assert r["positions"][1]["rotation"] == -90.0 and "angry" in " ".join(r["suggestions"])


async def test_interactive_pose_uses_recipe(scene, monkeypatch):
    from types import SimpleNamespace

    from daz_mcp_server.tools import figure
    seen = {}

    def apply(recipe, align_limb_targets=False):
        seen["recipe"] = recipe
        seen["align"] = align_limb_targets
        return SimpleNamespace(to_dict=lambda: {
            "prepared": {"validation_issues": []},
            "alignment_results": [{"anchor_name": "r_hand", "converged": True,
                                   "final_error": 0.1}]})
    scene.apply_interaction_recipe = apply
    for n in scene.nodes.values():
        n.position = {"x": 0.0, "y": 0.0, "z": 0.0}
    r = await figure.daz_interactive_pose("A", "B", "handshake", distance=60)
    assert seen["align"] is True and seen["recipe"].kind == "handshake"
    assert r["applied"] == ["spaced 60 cm apart", "handshake"]
    assert r["alignment"] == [{"anchor": "r_hand", "converged": True, "finalError": 0.1}]


async def test_scene_template_blocks_and_lights(scene, monkeypatch):
    from types import SimpleNamespace

    from daz_mcp_server import _cinematic_lighting
    lights = {}

    def get_or_create(sc, label, kind, create):
        lights[label] = SimpleNamespace(
            calls=[], set_position=lambda *p, label=label: lights[label].calls.append(("pos", p)),
            aim_at=lambda *p, label=label: lights[label].calls.append(("aim", p)),
            set_numeric_property=lambda n, v, label=label: lights[label].calls.append((n, v)))
        return lights[label], True
    monkeypatch.setattr(_cinematic_lighting, "_get_or_create_light", get_or_create)
    ground = {}
    monkeypatch.setattr("daz_mcp_server._client.get_daz_client", lambda: None)

    class RS:  # pylint: disable=too-few-public-methods
        def __init__(self, client):
            pass

        def __setattr__(self, name, value):
            ground[name] = value
    monkeypatch.setattr("dazpy.DazRenderSettings", RS)
    for n in scene.nodes.values():
        n.bounding_box = lambda: {"min": {"x": -20, "y": 0, "z": -10},
                                  "max": {"x": 20, "y": 170, "z": 10}}
    r = st.scene_template("A business interview", ["A", "B", "Ghost"])
    assert r["sceneType"] == "interview"
    assert ("1", "XTranslate", -80.0) in scene.batches[0]
    assert set(lights) == {"Key Light", "Fill Light", "Back Light"}
    assert ("Flux", 2200.0) in lights["Key Light"].calls
    assert ground == {"draw_ground_plane": False}
    r = st.scene_template("portrait", ["Ghost"])
    assert r["sceneType"] == "portrait" and "Applied" not in " ".join(r["actions"])
