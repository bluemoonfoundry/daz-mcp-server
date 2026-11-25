"""Unit tests (no Studio) for utility tools on dazpy: batch property set,
property inspection, scene validation and auto-improve (daz-mcp-server-ksl)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from dazpy import BatchPropertyResult, CheckFinding, CheckReport, PropertyDetails
from dazpy.exceptions import AmbiguousNodeError, NodeNotFoundError, PropertyNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import utility

XT = PropertyDetails("X Translate", "XTranslate", "DzFloatProperty", 0.0, -1e4, 1e4, 0.0,
                     "/General/Transforms/Translation", True)


def _box(x0, x1):
    return {"min": {"x": x0, "y": 0, "z": 0}, "max": {"x": x1, "y": 180, "z": 30}}


class FakeScene:
    def __init__(self):
        self.lights = []
        self.created = []
        self.findings: tuple = ()
        self.figures = [{"name": "Genesis9", "label": "Alice", "type": "DzFigure"},
                        {"name": "Genesis9_2", "label": "Bob", "type": "DzFigure"}]
        self.boxes = {"Alice": _box(0, 50), "Bob": _box(100, 150)}
        self.cameras = [{"name": "Camera", "label": "Camera"}]
        self.batch_calls = []

    def overview(self):
        return {"scene_file": "", "selected_node": None, "figures": self.figures,
                "cameras": self.cameras, "lights": self.lights, "total_nodes": 10}

    def check(self):
        return CheckReport(self.findings)

    def resolve_node(self, ref):
        if ref == "Twin":
            raise AmbiguousNodeError("Twin", 2, [])
        if ref not in self.boxes and ref != "Light":
            raise NodeNotFoundError(f"Node not found: {ref!r}")
        return SimpleNamespace(
            bounding_box=lambda: self.boxes[ref],
            describe=lambda: SimpleNamespace(label=ref),
            property_details=lambda kind="all": [XT],
            property_detail=self._detail)

    @staticmethod
    def _detail(name):
        if name.lower() not in ("xtranslate", "x translate"):
            raise PropertyNotFoundError(f"Property not found: {name!r}")
        return XT

    def set_numeric_properties(self, ops):
        self.batch_calls.append(list(ops))
        return [BatchPropertyResult(True, "Alice", "X Translate", 10.0),
                BatchPropertyResult(False, None, error="Property not found: Nope")]

    def create_light(self, light_type, name=None):
        light = SimpleNamespace(label=None)
        self.created.append((light_type, light))
        return light


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(utility, "get_scene", lambda: s)
    return s


async def test_batch_set_properties_one_call(scene):
    r = await utility.daz_batch_set_properties([
        {"nodeLabel": "Alice", "propertyName": "XTranslate", "value": 10},
        {"nodeLabel": "Alice", "propertyName": "Nope", "value": 1}])
    assert scene.batch_calls == [[("Alice", "XTranslate", 10), ("Alice", "Nope", 1)]]
    assert r["successCount"] == 1 and r["failureCount"] == 1 and r["total"] == 2
    assert r["results"][0] == {"success": True, "node": "Alice", "property": "X Translate",
                               "value": 10.0}
    assert r["results"][1] == {"success": False, "node": "Alice",
                               "error": "Property not found: Nope"}


async def test_batch_set_properties_rejects_malformed_ops(scene):
    with pytest.raises(ToolError, match="nodeLabel"):
        await utility.daz_batch_set_properties([{"propertyName": "X", "value": 1}])


async def test_inspect_properties(scene):
    r = await utility.daz_inspect_properties("Alice", "transform")
    assert r["node"] == "Alice" and r["count"] == 1
    assert r["properties"][0] == {"label": "X Translate", "name": "XTranslate",
                                  "type": "DzFloatProperty", "value": 0.0, "min": -1e4,
                                  "max": 1e4, "path": "/General/Transforms/Translation",
                                  "is_animatable": True}


async def test_inspect_properties_bad_type(scene):
    with pytest.raises(ToolError, match="property_type"):
        await utility.daz_inspect_properties("Alice", "colour")


async def test_property_metadata(scene):
    r = await utility.daz_get_property_metadata("Alice", "x translate")
    assert r["current_value"] == 0.0 and r["default_value"] == 0.0 and r["node"] == "Alice"
    with pytest.raises(ToolError, match="Property not found"):
        await utility.daz_get_property_metadata("Alice", "Nope")


async def test_validate_clean_scene(scene):
    scene.lights = [{"name": "L1", "label": "L1"}, {"name": "L2", "label": "L2"}]
    r = await utility.daz_validate_scene()
    assert r["valid"] is True and r["issues"] == [] and r["score"] == 100
    assert r["summary"] == {"figures": 2, "cameras": 1, "lights": 2, "lit": True}


async def test_validate_flags_collision_and_no_light(scene):
    scene.boxes["Bob"] = _box(40, 90)
    scene.findings = (CheckFinding("error", "no_light", "scene", "Nothing lights the render"),)
    r = await utility.daz_validate_scene()
    types = [i["type"] for i in r["issues"]]
    assert "collision" in types and "no_light" in types and r["valid"] is False
    collision = next(i for i in r["issues"] if i["type"] == "collision")
    assert collision["nodes"] == ["Alice", "Bob"]
    assert r["score_breakdown"]["lighting"] == 0 and r["score_breakdown"]["collision"] == 30
    assert r["summary"]["lit"] is False
    assert r["findings"][0]["code"] == "no_light"


async def test_validate_framing_warning_and_single_light(scene):
    scene.lights = [{"name": "L1", "label": "L1"}]
    scene.findings = (CheckFinding("warning", "subject_out_of_frame", "Alice",
                                   "Alice is partly out of frame", sides=("top",)),)
    r = await utility.daz_validate_scene()
    types = [w["type"] for w in r["warnings"]]
    assert types == ["subject_out_of_frame", "poor-lighting"]
    assert r["valid"] is True and r["score_breakdown"]["lighting"] == 50


async def test_validate_skips_ambiguous_figures(scene):
    scene.figures.append({"name": "T", "label": "Twin", "type": "DzFigure"})
    r = await utility.daz_validate_scene()
    assert r["summary"]["figures"] == 3


async def test_auto_improve_adds_light_for_no_light(scene):
    scene.findings = (CheckFinding("error", "no_light", "scene", "Nothing lights the render"),)
    r = await utility.daz_auto_improve_scene()
    assert r["fixed"] == ["Added missing light"] and r["count"] == 1
    light_type, light = scene.created[0]
    assert light_type == "distant" and light.label == "Auto Light"
