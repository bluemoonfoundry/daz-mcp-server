"""Unit tests (no Studio) for camera/light tools on dazpy (daz-mcp-server-qrd)."""
from __future__ import annotations

import math
from types import SimpleNamespace

import pytest
from dazpy import BatchPropertyResult, CameraInfo, LightInfo, NodeInfo, PropertyDetails
from dazpy.exceptions import NodeNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import camera_light as cl


class FakeNode:
    def __init__(self, label, eid, pos=(0.0, 0.0, 0.0), box=None):
        self.label = label
        self.eid = eid
        self._pos = dict(zip("xyz", pos))
        self.box = box
        self.calls = []
        self.props = {}
        self.focal_length = 65.0

    @property
    def position(self):
        return dict(self._pos)

    def describe(self):
        return NodeInfo(self.label, self.label, "DzBasicCamera", self.eid, None, 0)

    def set_position(self, x, y, z):
        self._pos = {"x": x, "y": y, "z": z}
        self.calls.append(("pos", (x, y, z)))

    def aim_at(self, x, y, z):
        self.calls.append(("aim", (x, y, z)))

    def bounding_box(self):
        return self.box

    def property_details(self, kind="all"):
        return [PropertyDetails(n, n, "DzFloatProperty", v, None, None, 0.0, "", True)
                for n, v in (("XTranslate", 1.0), ("YRotate", 30.0), ("Scale", 1.0))]

    def set_numeric_property(self, name, value, **_):
        self.props[name] = value

    def property_detail(self, name):
        return SimpleNamespace(value=self.props.get(name))

    def delete(self):
        self.calls.append(("delete", None))
        return True


class FakeScene:
    def __init__(self):
        self.nodes = {
            "Camera 1": FakeNode("Camera 1", 11),
            "Genesis 9": FakeNode("Genesis 9", 12, (0, 0, 0),
                                  {"min": {"x": -20, "y": 0, "z": -10},
                                   "max": {"x": 20, "y": 170, "z": 10}}),
        }
        self.viewport = "Perspective View"
        self.created = []
        self.batch = []
        self.lights_list = []

    def resolve_node(self, ref):
        for n in self.nodes.values():
            if ref in (n.label, str(n.eid)):
                return n
        raise NodeNotFoundError(f"Node not found: {ref!r}")

    def find_nodes(self, name):  # label or internal name (label with "_" for spaces)
        return [n for n in self.nodes.values() if name in (n.label, n.label.replace(" ", "_"))]

    def set_viewport_camera(self, label):
        if label not in self.nodes and label != "Perspective View":
            raise NodeNotFoundError(f"Camera not found: {label!r}")
        prev, self.viewport = self.viewport, label
        return prev

    def viewport_camera(self):
        return SimpleNamespace(label=self.viewport)

    def set_numeric_properties(self, ops):
        self.batch.append(list(ops))
        return [BatchPropertyResult(name != "Bogus", "Camera 1", name, v) for _, name, v in ops]

    def camera_info(self):
        return [CameraInfo(0, "Camera 1", "Camera_1", "DzBasicCamera", 11, (0.0, 150.0, 300.0),
                           65.0)]

    def light_info(self):
        return list(self.lights_list)

    def lights(self):
        return [SimpleNamespace(intensity=None, colors=[],
                                set_color=lambda *c: None) for _ in range(2)]

    def create_light(self, kind, name=None):
        node = FakeNode(name or kind, 100 + len(self.created))
        self.created.append((kind, name, node))
        return node

    def create_camera(self, name=None):
        node = FakeNode(name or "Camera", 200 + len(self.created))
        self.created.append(("camera", name, node))
        return node


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(cl, "get_scene", lambda: s)
    return s


async def test_set_active_camera(scene):
    r = await cl.daz_set_active_camera("Camera 1")
    assert r == {"success": True, "camera": "Camera 1", "previousCamera": "Perspective View"}
    with pytest.raises(ToolError, match="Camera not found"):
        await cl.daz_set_active_camera("Nope")


async def test_orbit(scene):
    r = await cl.daz_orbit_camera_around("Camera 1", "Genesis 9", 200, 90, 0)
    assert r["position"]["x"] == pytest.approx(200) and r["position"]["z"] == pytest.approx(0)
    assert scene.nodes["Camera 1"].calls[-1] == ("aim", (0, 0, 0))


async def test_frame_camera_to_node(scene):
    r = await cl.daz_frame_camera_to_node("Camera 1", "Genesis 9")
    assert r["nodeCenter"] == {"x": 0, "y": 85, "z": 0}
    assert r["position"]["z"] == pytest.approx(170 * 2.5)


async def test_camera_preset_round_trip(scene):
    saved = await cl.daz_save_camera_preset("Camera 1")
    assert saved["preset"]["transforms"] == {"XTranslate": 1.0, "YRotate": 30.0}
    r = await cl.daz_load_camera_preset("Camera 1", {"transforms": {"XTranslate": 5.0,
                                                                     "Bogus": 1}})
    assert scene.batch == [[("11", "XTranslate", 5.0), ("11", "Bogus", 1)]]
    assert r == {"success": True, "camera": "Camera 1", "applied": ["XTranslate"]}
    with pytest.raises(ToolError, match="Invalid preset"):
        await cl.daz_load_camera_preset("Camera 1", {"oops": 1})


async def test_list_cameras_and_lights(scene):
    scene.lights_list = [LightInfo(0, "Key", "Key", "DzSpotLight", 7, (1.234, 2.0, 3.0),
                                   1999.6, True)]
    cams = await cl.daz_list_cameras()
    assert cams["cameras"][0]["focal_length"] == 65.0
    lights = await cl.daz_list_lights()
    assert lights["lights"][0] == {"index": 0, "label": "Key", "name": "Key",
                                   "type": "DzSpotLight",
                                   "position": {"x": 1.23, "y": 2.0, "z": 3.0},
                                   "flux": 2000, "enabled": True}


async def test_create_light_and_camera(scene):
    r = await cl.daz_create_light("spot", "Key Light", flux=1500, aim_at_label="Genesis 9")
    kind, name, light = scene.created[0]
    assert (kind, name, light.label) == ("spot", "Key_Light", "Key Light")
    assert light.props["Flux"] == 1500.0 and light.calls[-1] == ("aim", (0.0, 85.0, 0.0))
    assert r["flux"] == 1500.0
    r = await cl.daz_create_camera("Camera 1", focal_length=85)
    assert scene.created[1][1] == "Camera_1_2"  # label in use -> unique name
    assert r["focal_length"] == 85


async def test_lighting_preset(scene, monkeypatch):
    monkeypatch.setattr(cl, "DazRenderSettings",
                        lambda client: SimpleNamespace(set_environment_mode=lambda m: True))
    monkeypatch.setattr(cl, "get_daz_client", lambda: None)
    scene.lights_list = [LightInfo(0, "Key Light", "Key", "DzSpotLight", 12, (0, 0, 0), 1.0,
                                   True)]
    r = await cl.daz_apply_lighting_preset("rembrandt", "Genesis 9")
    assert [c["label"] for c in r["lights_created"]] == ["Key Light", "Fill Light"]
    assert scene.nodes["Genesis 9"].calls[-1] == ("delete", None)  # old Key Light removed
    key = scene.created[0][2]
    assert key.props == {"Flux": 2200.0, "Shadow Softness": 20.0}
    face_y = 85 + 170 * 0.2
    assert key.calls[-1] == ("aim", (0.0, pytest.approx(face_y), 0.0))
    expected_y = 85 + 204 * math.sin(math.radians(45)) + 17
    assert key.calls[0][1][1] == pytest.approx(expected_y)
    assert r["environment_mode"] == "Scene Only (3)"


async def test_mood_and_time_of_day(scene):
    r = await cl.daz_set_mood_lighting("romantic")
    assert r["lights_adjusted"] == 2 and r["mood"] == "romantic"
    r = await cl.daz_apply_time_of_day("noon")
    assert r["lights_adjusted"] == 2
