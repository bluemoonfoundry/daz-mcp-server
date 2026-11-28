"""Unit tests (no Studio) for the cinematic lighting tools on dazpy
(daz-mcp-server-ord, lighting slice)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from dazpy import NodeInfo, NumericCandidateMatch
from dazpy.exceptions import NodeNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server import _cinematic_lighting as cl
from daz_mcp_server.tools import cinematic


class FakeLight:
    def __init__(self, label, flux=True):
        self.label, self.flux = label, flux
        self.flux_keys, self.color_keys, self.props, self.calls = [], [], {}, []
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}

    def describe(self):
        return NodeInfo(self.label, self.label, "DzSpotLight", 1, None, 0)

    def key_numeric_candidates(self, slots):
        names, keys = slots[0]
        if not self.flux:
            return [NumericCandidateMatch(tuple(names), 0.0, None, None, None)]
        self.flux_keys = list(keys)
        return [NumericCandidateMatch(tuple(names), 0.0, "Flux", "property", None)]

    def key_color(self, name, keys):
        self.color_keys = list(keys)
        return len(keys)

    def set_position(self, x, y, z):
        self.calls.append(("pos", (x, y, z)))

    def aim_at(self, x, y, z):
        self.calls.append(("aim", (x, y, z)))

    def set_numeric_property(self, name, value, **_):
        self.props[name] = value


class FakeScene:
    def __init__(self):
        self.nodes = {"Key": FakeLight("Key"), "Lamp": FakeLight("Lamp", flux=False),
                      "Alice": FakeLight("Alice")}
        self.nodes["Alice"].position = {"x": 10.0, "y": 0.0, "z": 0.0}
        self.created = []

    def resolve_node(self, ref):
        for n in self.nodes.values():
            if ref in (n.label, f"id:{n.label}"):
                return n
        raise NodeNotFoundError(f"Node not found: {ref!r}")

    def find_nodes(self, label):
        if label not in self.nodes:
            return []
        return [SimpleNamespace(label=label, element_id=f"id:{label}")]

    def create_light(self, kind, name=None):
        light = FakeLight(name or kind)
        self.created.append((kind, name, light))
        self.nodes[name] = light
        return light


class FakeRS:
    env = True
    calls: list = []

    def __init__(self, client=None):
        FakeRS.calls = []

    def set_environment_mode(self, mode):
        FakeRS.calls.append(("mode", mode))
        return FakeRS.env

    def set_environment_properties(self, settings):
        FakeRS.calls.append(("props", settings))
        return [names[0] for names, _ in settings] if FakeRS.env else None

    @property
    def environment_mode(self):
        return "scene_only"


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(cl, "get_scene", lambda: s)
    monkeypatch.setattr(cl, "get_daz_client", lambda: None)
    monkeypatch.setattr(cl, "DazRenderSettings", FakeRS)
    FakeRS.env = True
    return s


async def test_fade_in_keys_frames_not_ticks(scene):
    r = await cinematic.daz_animate_light("Key", "fade-in", 0, 30, 1500.0)
    assert scene.nodes["Key"].flux_keys == [(0, 0.0), (30, 1500.0)]
    assert r["keyframesCreated"] == 2


def test_flicker_and_pulse_and_strobe_shapes():
    assert cl.flicker_keys(0, 20, 100, 0.0, lambda: 0.5)[-1] == (20, 100)
    pulse = cl.pulse_keys(0, 40, 100, 0.5, 2)
    assert pulse[0] == (0, pytest.approx(75.0)) and len(pulse) == 9
    assert cl.strobe_keys(0, 10, 50, 5) == [(0, 50), (4, 50), (5, 0.0), (9, 0.0), (10, 50)]


async def test_color_cycle_keys_light_color(scene):
    r = await cinematic.daz_animate_light("Key", "color-cycle", 0, 90)
    keys = scene.nodes["Key"].color_keys
    assert keys[0] == (0, (255.0, 204.0, 127.5)) and len(keys) == 4
    assert r["keyframes"][2] == {"frame": 59, "r": 0.5, "g": 0.7, "b": 1.0}


async def test_light_without_flux_is_error(scene):
    with pytest.raises(ToolError, match="no Flux"):
        await cinematic.daz_animate_light("Lamp", "fade-out", 0, 10)


async def test_light_sequence_creates_and_keys(scene):
    r = await cinematic.daz_create_light_sequence("day-to-night", None, 0, 120)
    assert r["lightsCreated"] == ["Sun_Key", "Sky_Fill"]
    assert scene.nodes["Sun_Key"].flux_keys == [(0, 8000.0), (30, 6000.0), (60, 3000.0),
                                                (90, 800.0), (120, 0.0)]
    assert scene.created[0][0] == "distant" and r["totalKeyframes"] == 8


async def test_light_sequence_without_creating(scene):
    r = await cinematic.daz_create_light_sequence("interrogation", None, 0, 40,
                                                  create_lights=False)
    assert r["lightsCreated"] == [] and r["totalKeyframes"] == 0


async def test_atmosphere(scene):
    r = await cinematic.daz_set_scene_atmosphere(environment_mode=0, environment_intensity=0.4,
                                                 draw_dome=False)
    assert FakeRS.calls[0] == ("mode", "dome_and_scene")
    assert r["changeCount"] == 3 and "Dome and Scene" in r["changesApplied"][0]


async def test_atmosphere_without_environment_node(scene):
    FakeRS.env = False
    with pytest.raises(ToolError, match="No environment node"):
        await cinematic.daz_set_scene_atmosphere(environment_mode=3)


async def test_visual_style(scene):
    r = await cinematic.daz_apply_visual_style("noir", "Alice", 1.0)
    key = scene.nodes["Style_Key"]
    assert key.props == {"Flux": 4000.0, "Shadow Softness": 0.1}
    assert key.calls[-1] == ("aim", (10.0, 130.0, 0.0))
    assert r["lightingRatios"]["key"] == 4000 and r["environmentMode"] == 3
