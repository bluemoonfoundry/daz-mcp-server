"""Unit tests for the cinematic tools that run on dazpy.shot_library (no Studio)."""
from __future__ import annotations

import math

import pytest
from dazpy import shot_library as sl
from dazpy.exceptions import NodeNotFoundError
from dazpy.math3 import Quat, Vec3
from dazpy.shots import framing_distance
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import camera_light, cinematic


class FakeNode:
    def __init__(self, pos, height=175.0, figure=True):
        self.position = {"x": pos[0], "y": pos[1], "z": pos[2]}
        self._bb = {"min": {"x": pos[0] - 25, "y": pos[1], "z": pos[2] - 15},
                    "max": {"x": pos[0] + 25, "y": pos[1] + height, "z": pos[2] + 15}}
        self.figure = figure

    def bounding_box(self):
        return self._bb


class FakeCamera:
    """Records every call; exposes a pose like a DazCamera."""

    def __init__(self, pos=(0.0, 150.0, 300.0), quat=(0.0, 0.0, 0.0, 1.0), focal_length=50.0):
        d = self.__dict__
        d["calls"] = []
        d["position"] = {"x": pos[0], "y": pos[1], "z": pos[2]}
        d["rotation"] = dict(zip("xyzw", quat))
        d["focal_length"] = focal_length
        d["f_stop"] = 8.0

    def __setattr__(self, name, value):
        self.calls.append(("set", name, value))
        self.__dict__[name] = value

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return lambda *a, **kw: self.calls.append((name,) + a + ((kw,) if kw else ()))

    def call(self, name):
        return [c for c in self.calls if c[0] == name]

    def last_set(self, name):
        return [c[2] for c in self.calls if c[:2] == ("set", name)][-1]


class FakeScene:
    def __init__(self, nodes, cameras=None):
        self.nodes, self.cameras, self.created, self.groups = nodes, dict(cameras or {}), [], []

    def find_skeleton_by_label(self, label):
        n = self.nodes.get(label)
        if n is None or not n.figure:
            raise NodeNotFoundError(label)
        return n

    def find_node_by_label(self, label):
        if label not in self.nodes:
            raise NodeNotFoundError(label)
        return self.nodes[label]

    find_node = find_node_by_label

    def find_camera_by_label(self, label):
        if label not in self.cameras:
            raise NodeNotFoundError(label)
        return self.cameras[label]

    def create_camera(self, name=None):
        cam = FakeCamera()
        self.created.append((name, cam))
        return cam

    def set_anim_range(self, *a):
        pass

    def overview(self):
        return {"figures": [{"name": k, "label": k} for k, n in self.nodes.items() if n.figure],
                "cameras": [{"name": k, "label": k} for k in self.cameras], "lights": []}

    def create_group(self, name, label=None, position=None):
        group = FakeNode(position, figure=False)
        self.groups.append((name, label, position))
        self.nodes[name if label is None else label] = group
        return group


@pytest.fixture
def scene(monkeypatch):
    sc = FakeScene({"Alice": FakeNode((0, 0, 0)), "Bob": FakeNode((0, 0, -120)),
                    "Cup": FakeNode((30, 90, -60), height=10, figure=False)},
                   {"Camera 1": FakeCamera()})
    monkeypatch.setattr(camera_light, "get_scene", lambda: sc)
    monkeypatch.setattr(cinematic, "get_scene", lambda: sc)
    return sc


def pos_of(cam):
    return Vec3(*cam.call("set_position")[-1][1:])


def aim_of(cam):
    return Vec3(*cam.call("aim_at")[-1][1:])


async def test_frame_shot_fits_size_to_current_lens(scene):
    out = await camera_light.daz_frame_shot("Camera 1", "Alice", "close-up")
    cam = scene.cameras["Camera 1"]
    p, aim = pos_of(cam), aim_of(cam)
    assert p.z > 0 and abs(p.x) < 1e-6  # in front of a +Z-facing figure
    assert p.distance(aim) == pytest.approx(framing_distance("close_up", 50.0))
    assert aim.y == pytest.approx(sl.SHOT_SIZES["close_up"][1])
    assert out["framing"] == "face and head" and out["shot"]["id"] == "CU_Alice"
    assert cam.last_set("focal_length") == 50.0  # lens kept


async def test_frame_shot_prop_aims_at_centre(scene):
    await camera_light.daz_frame_shot("Camera 1", "Cup", "extreme-close-up")
    assert aim_of(scene.cameras["Camera 1"]) == Vec3(30, 95, -60)


async def test_composition_rule_places_eyes_on_the_rule(scene):
    out = await camera_light.daz_apply_composition_rule("Camera 1", "Alice", "golden-ratio")
    cam = scene.cameras["Camera 1"]
    p, aim = pos_of(cam), aim_of(cam)
    eye = Vec3(0, sl.EYE_HEIGHT_CM, 0)
    fwd = (aim - p).normalize()
    right = fwd.cross(Vec3(0, 1, 0)).normalize()
    half_width = sl.DEFAULT_FRAME_WIDTH_MM / sl.DEFAULT_ASPECT / 50 / 2  # frame width spans the height
    x = (eye - p).dot(right) / (eye - p).dot(fwd) / half_width
    assert x == pytest.approx(sl.GOLDEN_X, abs=1e-6)
    assert math.hypot(p.x, p.z) == pytest.approx(300, abs=1e-6)  # kept its distance
    assert out["rule"] == "golden-ratio"


async def test_dutch_angle_rolls_about_the_lens_axis(scene):
    await camera_light.daz_apply_camera_angle("Camera 1", "Alice", "dutch-angle")
    cam = scene.cameras["Camera 1"]
    rot = cam.call("set_rotation")[-1][1:]
    p = pos_of(cam)
    assert sl.forward_from_rotation(rot).dot((Vec3(0, sl.EYE_HEIGHT_CM, 0) - p).normalize()) == pytest.approx(1)
    assert math.degrees(math.acos(sl.camera_up(rot).dot(Vec3(0, 1, 0)))) == pytest.approx(15, abs=1e-6)


async def test_over_shoulder_angle_stands_behind_subject(scene):
    out = await camera_light.daz_apply_camera_angle("Camera 1", "Alice", "over-shoulder")
    assert out["camera_position"]["z"] < 0  # behind a +Z-facing figure


async def test_shot_reverse_shot_keeps_cameras_on_one_side(scene):
    for side in (1, -1):
        scene.created.clear()
        out = await cinematic.daz_create_shot_sequence("shot-reverse-shot", ["Alice", "Bob"], 240, side=side)
        assert [c["label"] for c in out["cameras"]] == ["OTS_Bob_over_Alice", "OTS_Alice_over_Bob"]
        assert [c["frameRange"] for c in out["cameras"]] == [{"start": 0, "end": 119},
                                                             {"start": 120, "end": 239}]
        assert out["continuity"] == []
        line = sl.LineOfAction("Alice", "Bob", Vec3(0, 0, 0), Vec3(0, 0, -120), side)
        assert all(line.side_of(pos_of(cam)) == side for _, cam in scene.created)
        assert [n for n, _ in scene.created] == ["OTS_Bob_over_Alice", "OTS_Alice_over_Bob"]


async def test_establishing_and_moves(scene):
    est = await cinematic.daz_create_shot_sequence("establishing-medium-closeup", ["Alice"], 180)
    assert [(c["label"], c["frameRange"]["start"]) for c in est["cameras"]] == [
        ("WS_Alice", 0), ("MS_Alice", 60), ("CU_Alice", 120)]
    orbit = await cinematic.daz_create_shot_sequence("orbit", ["Alice"], 300)
    assert orbit["cameras"][0]["animated"]
    assert len(scene.created[-1][1].call("set_position_at_frame")) == 25  # every 15 degrees
    push = await cinematic.daz_create_shot_sequence("push-in", [], 120)
    assert push["subject"] is None and push["cameras"][0]["label"] == "PUSH_origin"


async def test_shot_coverage(scene):
    out = await cinematic.daz_setup_shot_coverage("Alice", "dramatic", camera_height=150)
    assert [c["label"] for c in out["cameras"]] == ["WS_Alice", "MS_low_Alice", "MS_high_Alice",
                                                    "MCU_profile_Alice"]
    assert out["cameraCount"] == 4
    assert all(aim_of(cam).y == pytest.approx(150) for _, cam in scene.created[:1])


BEATS = [
    {"speaker": "Alice", "start": 0, "end": 59, "line": "You came back."},
    {"speaker": "Bob", "start": 60, "end": 119, "line": "I had to."},
    {"speaker": "Alice", "start": 120, "end": 179},
]


async def test_cover_conversation_cuts_beats_on_one_side(scene):
    for side in (1, -1):
        scene.created.clear()
        out = await cinematic.daz_cover_conversation("Alice", "Bob", BEATS, side=side,
                                                     establish_frames=24)
        assert out["mode"] == "conversation" and out["continuity"] == []
        cut = [(c.pop("shot"), c.pop("camera"), c) for c in out["cutList"]]
        assert all(shot == cam for shot, cam, _ in cut)
        assert [(shot, rest) for shot, _, rest in cut] == [
            ("000_MST_Alice-Bob", {"start": 0, "end": 23}),
            ("001_OTS_Alice_over_Bob",
             {"start": 24, "end": 59, "speaker": "Alice", "line": "You came back."}),
            ("002_OTS_Bob_over_Alice",
             {"start": 60, "end": 119, "speaker": "Bob", "line": "I had to."}),
            ("003_OTS_Alice_over_Bob", {"start": 120, "end": 179, "speaker": "Alice"}),
        ]
        line = sl.LineOfAction("Alice", "Bob", Vec3(0, 0, 0), Vec3(0, 0, -120), side)
        assert len(scene.created) == 4
        assert all(line.side_of(pos_of(cam)) == side for _, cam in scene.created)


async def test_cover_conversation_singles_and_lens(scene):
    out = await cinematic.daz_cover_conversation("Alice", "Bob", BEATS[:2], style="singles",
                                                 single_size="close-up", focal_length=85)
    assert [c["shot"] for c in out["cutList"]] == ["001_CU_Alice", "002_CU_Bob"]
    assert {c["focalLength"] for c in out["cameras"]} == {85}


async def test_cover_conversation_reports_jump_cuts(scene):
    # Same speaker twice in a row: the second cut barely moves the camera.
    beats = [{"speaker": "Alice", "start": 0, "end": 29},
             {"speaker": "Alice", "start": 30, "end": 59}]
    out = await cinematic.daz_cover_conversation("Alice", "Bob", beats)
    assert [i["kind"] for i in out["continuity"]] == ["thirty_degree"]
    assert out["continuity"][0]["previousShot"] == "001_OTS_Alice_over_Bob"


async def test_cover_conversation_without_beats_sets_up_coverage(scene):
    out = await cinematic.daz_cover_conversation("Alice", "Bob", include=["master", "singles"])
    assert out["mode"] == "coverage" and "cutList" not in out
    assert [c["label"] for c in out["cameras"]] == ["MST_Alice-Bob", "MCU_Alice", "MCU_Bob"]
    assert out["continuity"] == []


@pytest.mark.parametrize("kwargs, message", [
    ({"beats": [{"speaker": "Carol", "start": 0, "end": 10}]}, "must be 'Alice' or 'Bob'"),
    ({"beats": [{"speaker": "Alice", "start": 0}]}, "missing field"),
    ({"beats": [{"speaker": "Alice", "start": 0, "end": 30},
                {"speaker": "Bob", "start": 30, "end": 60}]}, "before beat 1 ends"),
    ({"style": "wide"}, "style must be"),
    ({"side": 0}, "side must be"),
    ({"include": ["closeups"]}, "Unknown include"),
    ({"single_size": "huge"}, "single_size must be"),
])
async def test_cover_conversation_rejects_bad_input(scene, kwargs, message):
    with pytest.raises(ToolError, match=message):
        await cinematic.daz_cover_conversation("Alice", "Bob", **kwargs)
    assert not scene.created


async def test_camera_movement_chains_and_pans_right(scene):
    q = Quat.from_euler(0, 30, 0, order="ZYX").conjugate()  # as Studio's getWSRot reports it
    cam = FakeCamera(quat=(q.x, q.y, q.z, q.w))
    scene.cameras["Cam"] = cam
    out = await cinematic.daz_animate_camera_movement("Cam", "pan-right", 10, 40, intensity=0.5)
    rots = cam.call("set_rotation_at_frame")
    assert [r[1] for r in rots] == [10, 40]
    assert rots[0][3] == pytest.approx(30) and rots[1][3] == pytest.approx(30 - 22.5)
    assert not cam.call("clear_position_keys") and not cam.call("clear_rotation_keys")
    assert out["keyframesSet"] == 2 and "22" in out["description"]


async def test_handheld_is_repeatable(scene):
    a = await cinematic.daz_animate_camera_movement("Camera 1", "handheld-shake", 0, 30)
    b = await cinematic.daz_animate_camera_movement("Camera 1", "handheld-shake", 0, 30)
    assert a == b and a["keyframesSet"] == 11


async def test_focus_point_on_eyes(scene):
    out = await cinematic.daz_set_focus_point("Camera 1", target_label="Bob", f_stop=2.8)
    expected = Vec3(0, 150, 300).distance(Vec3(0, sl.EYE_HEIGHT_CM, -120))
    assert out["focalDistance"] == pytest.approx(expected, abs=0.05)
    near, far = sl.depth_of_field_limits(50, 2.8, out["focalDistance"])
    assert out["dofPreview"]["nearSharp"] == pytest.approx(near, abs=0.05)
    assert scene.cameras["Camera 1"].last_set("depth_of_field") is True


async def test_focus_pull_keys_and_phases(scene):
    out = await cinematic.daz_animate_focus_pull("Camera 1", from_target="Alice", to_distance=500,
                                                 start_frame=0, end_frame=60,
                                                 hold_from_frames=10, hold_to_frames=10)
    keys = scene.cameras["Camera 1"].call("set_focal_distance_at_frame")
    assert [k[1] for k in keys] == [0, 10, 50, 60]
    assert [k["phase"] for k in out["keyframes"]] == ["hold-from", "pull-start", "pull-end", "hold-to"]
    assert out["toDistance"] == 500 and out["pullDurationFrames"] == 40
    plain = await cinematic.daz_animate_focus_pull("Camera 1", from_distance=100, to_distance=200)
    assert [k["phase"] for k in plain["keyframes"]] == ["pull-start", "pull-end"]


@pytest.mark.parametrize("call", [
    lambda: camera_light.daz_frame_shot("Camera 1", "Alice", "cowboy"),
    lambda: camera_light.daz_apply_camera_angle("Camera 1", "Alice", "sideways"),
    lambda: camera_light.daz_frame_shot("Camera 1", "Nobody"),
    lambda: camera_light.daz_frame_shot("No Cam", "Alice"),
    lambda: cinematic.daz_create_shot_sequence("shot-reverse-shot", ["Alice"]),
    lambda: cinematic.daz_create_shot_sequence("shot-reverse-shot", ["Alice", "Alice"]),
    lambda: cinematic.daz_create_shot_sequence("orbit", ["Alice"], side=0),
    lambda: cinematic.daz_animate_camera_movement("Camera 1", "zoom"),
    lambda: cinematic.daz_animate_focus_pull("Camera 1", from_distance=-1, to_distance=10),
])
async def test_errors_are_tool_errors(scene, call):
    with pytest.raises(ToolError):
        await call()


# ---- m0n3: plan_shot / storyboard / camera rig / camera path / create_scene ----

async def test_plan_shot_is_read_only_and_returns_a_shot(scene):
    out = await cinematic.daz_plan_shot("close-up", "Alice", "Camera 1", mood="dramatic",
                                        composition_rule="center-frame")
    assert scene.created == [] and not scene.cameras["Camera 1"].calls  # nothing applied
    cam = out["recommendations"]["camera"]
    assert cam["focalLength"] == 85.0 and cam["position"]["z"] > 0  # in front of Alice
    assert cam["distanceFromSubject"] == pytest.approx(framing_distance("close_up", 85.0), abs=0.1)
    assert out["shot"]["id"] == "CU_Alice" and out["shot"]["camera"]["size"] == "close_up"
    assert out["recommendations"]["lighting"]["preset"] == "rembrandt"
    assert {f["label"] for f in out["sceneState"]["figures"]} == {"Alice", "Bob"}
    assert out["recommendations"]["toolSequence"][0] == 'daz_frame_shot("Camera 1", "Alice", "close-up")'


async def test_plan_shot_pairs_with_nearest_figure(scene):
    ots = await cinematic.daz_plan_shot("over-shoulder", "Alice")
    assert ots["shot"]["id"] == "OTS_Alice_over_Bob"
    assert ots["recommendations"]["camera"]["position"]["z"] < -120  # behind Bob, looking at Alice
    golden = await cinematic.daz_plan_shot("medium-shot", "Alice", composition_rule="golden-ratio")
    assert golden["shot"]["camera"]["kind"] == "placement"
    thirds = await cinematic.daz_plan_shot("wide-shot")
    assert thirds["subject"] is None and thirds["shot"]["camera"]["composition"] == "right_third"


async def test_storyboard_applies_shots_with_frame_ranges(scene):
    out = await cinematic.daz_create_storyboard("Cafe", [
        {"label": "Est", "shotType": "wide-shot", "subjectLabel": "Alice", "durationFrames": 60},
        {"shot_type": "close-up", "subject": "Alice", "angle": 90, "dialogue": "Hi."},
        {"shotType": "over-shoulder", "subjectLabel": "Bob", "camera": "Camera 1"},
        {"shotType": "two-shot", "subjectLabel": "Alice"},
    ], frames_per_shot=30)
    assert out["shots"][3]["shotId"] == "004_2S_Alice-Bob"
    assert [(s["startFrame"], s["endFrame"]) for s in out["shots"]] == [(0, 59), (60, 89), (90, 119),
                                                                        (120, 149)]
    assert out["cameras"] == ["Cafe_Cam1", "Cafe_Cam2", "Camera 1", "Cafe_Cam4"]
    assert [s["cameraCreated"] for s in out["shots"]] == [True, True, False, True]
    assert [n for n, _ in scene.created] == ["Cafe_Cam1", "Cafe_Cam2", "Cafe_Cam4"]
    cu = pos_of(scene.created[1][1])
    assert cu.x > 0 and abs(cu.z) < 1e-6  # angle 90 = the subject's +X side
    assert out["shots"][2]["shotId"] == "003_OTS_Bob_over_Alice"
    seq = out["sequence"]["shots"]
    assert seq[1]["storyboard"]["dialogue"] == "Hi." and seq[0]["frame_range"] == [0, 59]
    plan_only = await cinematic.daz_create_storyboard("P", [{"shotType": "medium-shot"}],
                                                      save_presets=False)
    assert plan_only["cameras"] == [] and len(scene.created) == 3


async def test_camera_rig_aims_every_camera_at_centre(scene):
    out = await cinematic.daz_create_camera_rig("Rig", {"x": 0, "y": 100, "z": 0}, camera_count=4,
                                                radius=200, height_variation=0, focal_lengths=[35])
    assert [c["label"] for c in out["cameras"]] == ["Rig_Cam1", "Rig_Cam2", "Rig_Cam3", "Rig_Cam4"]
    assert [c["focalLength"] for c in out["cameras"]] == [35.0, 50.0, 50.0, 50.0]
    for (_, cam), angle in zip(scene.created, (0, 90, 180, 270)):
        p = pos_of(cam)
        assert aim_of(cam) == Vec3(0, 100, 0)
        assert p.distance(Vec3(0, 100, 0)) == pytest.approx(200)
        assert math.degrees(math.atan2(p.x, p.z)) % 360 == pytest.approx(angle % 360, abs=1e-6)
        assert cam.call("reparent")
    assert scene.groups == [("Rig_Rig", None, (0.0, 100.0, 0.0))]


async def test_camera_rig_reuses_an_existing_group(scene):
    rig = FakeNode((0, 0, 0), figure=False)
    scene.nodes["Rig_Rig"] = rig
    await cinematic.daz_create_camera_rig("Rig", {"x": 0, "y": 100, "z": 0}, camera_count=2)
    assert scene.groups == []
    assert all(cam.call("reparent")[0][1] is rig for _, cam in scene.created)


async def test_camera_path_keys_waypoints_and_tracks_target(scene):
    cam = scene.cameras["Camera 1"]
    out = await cinematic.daz_create_camera_path("Camera 1", [
        {"position": {"x": 100, "y": 160, "z": 300}, "frame": 60},
        {"position": {"x": 0, "y": 160, "z": 400}, "frame": 0},
    ], aim_at_target="Alice")
    assert [k[1:] for k in cam.call("set_position_at_frame")] == [(0, 0.0, 160.0, 400.0),
                                                                  (60, 100.0, 160.0, 300.0)]
    assert len(cam.call("set_rotation_at_frame")) == 2 and cam.call("clear_rotation_keys")
    assert out["frameRange"] == {"start": 0, "end": 60} and out["keyframesSet"] == 12
    assert out["aimPoint"]["y"] == sl.EYE_HEIGHT_CM
    with pytest.raises(ToolError):
        await cinematic.daz_create_camera_path("Camera 1", [
            {"position": {"x": 0, "y": 0, "z": 0}, "frame": 5},
            {"position": {"x": 1, "y": 0, "z": 0}, "frame": 5}])


@pytest.mark.parametrize("scene_type,ids", [
    ("conversation", ["OTS_Bob_over_Alice", "OTS_Alice_over_Bob"]),
    ("dining", ["MST_Alice-Bob", "OTS_Bob_over_Alice"]),
    ("interview", ["MST_Alice-Bob", "MS_Alice"]),
])
async def test_create_scene_builds_cameras_with_dazpy(scene, monkeypatch, scene_type, ids):
    def fake_template(description, characters):
        return {"sceneType": scene_type, "actions": [], "suggestions": []}
    monkeypatch.setattr("daz_mcp_server._cinematic_staging.scene_template", fake_template)
    out = await cinematic.daz_create_scene("a scene", ["Alice", "Bob", "Ghost"])
    assert [c["label"] for c in out["cameras"]] == ids
    assert out["continuity"] == []
    assert [n for n, _ in scene.created] == ids
    none = await cinematic.daz_create_scene("portrait", ["Ghost"])
    assert none["cameras"] == [] and "Ghost" in none["suggestions"][-1]
