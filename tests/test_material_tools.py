"""Unit tests (no Studio) for the material tools on dazpy (daz-mcp-server-et7)."""
from __future__ import annotations

import json

import pytest
from dazpy import MaterialInfo, MaterialProperty, MaterialPropertyWrite, NodeInfo
from dazpy.exceptions import MaterialError, NodeNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import material

SKIN = MaterialInfo(0, "1_Skin", "Skin", "DzUberIrayMaterial")
LIPS = MaterialInfo(1, "2_Lips", "Lips", "DzDefaultMaterial")


class FakeMaterial:
    def __init__(self, info):
        self.info = info
        self.writes = []
        self.copied_from = None

    def describe(self):
        return MaterialInfo(None, self.info.name, self.info.label, self.info.shader)

    def property_values(self):
        return [MaterialProperty("Diffuse Color", "Base Color", "color", "#7a7a7a"),
                MaterialProperty("Glossy Roughness", "Glossy Roughness", "numeric", 0.3)]

    def set_property_value(self, name, value):
        if name == "Nope":
            raise MaterialError("Property not found: Nope")
        self.writes.append((name, value))
        kind = "color" if isinstance(value, str) else "numeric"
        return MaterialPropertyWrite(name, kind, value.lower() if kind == "color" else value)

    def copy_from(self, source):
        self.copied_from = source
        return (120, 1)


class FakeNode:
    def __init__(self, label, mats):
        self.label = label
        self.mats = {m.label: FakeMaterial(m) for m in mats}
        self.presets = []

    def describe(self):
        return NodeInfo(self.label, self.label, "DzFigure", 1, None, 0)

    def material_info(self):
        return [m.info for m in self.mats.values()]

    def resolve_material(self, ref):
        if ref in self.mats:
            return self.mats[ref]
        raise MaterialError(f"Material {ref!r} not found. Available: {', '.join(self.mats)}")

    def apply_surface_preset(self, path, *, map_paths=None, allow_missing=False):
        self.presets.append((path, list(map_paths or []), allow_missing))
        return [MaterialInfo(0, "1_Skin", "Skin", "DzUberIrayMaterial"),
                MaterialInfo(1, "2_Lips", "Lips", "DzUberIrayMaterial")]


class FakeScene:
    def __init__(self):
        self.nodes = {"Genesis 9": FakeNode("Genesis 9", [SKIN, LIPS]),
                      "Clone": FakeNode("Clone", [SKIN])}

    def resolve_node(self, ref):
        if ref not in self.nodes:
            raise NodeNotFoundError(f"Node not found: {ref!r}")
        return self.nodes[ref]

    def content_path(self, rel):
        return "D:/Lib/" + rel if "Iray Uber Base" in rel else None


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(material, "get_scene", lambda: s)
    return s


async def test_list_materials(scene):
    r = await material.daz_list_materials("Genesis 9")
    assert r == {"node": "Genesis 9", "material_count": 2, "materials": [
        {"index": 0, "name": "1_Skin", "label": "Skin", "shader": "DzUberIrayMaterial"},
        {"index": 1, "name": "2_Lips", "label": "Lips", "shader": "DzDefaultMaterial"}]}


async def test_list_materials_missing_node(scene):
    with pytest.raises(ToolError, match="Node not found"):
        await material.daz_list_materials("Ghost")


async def test_get_material(scene):
    r = await material.daz_get_material("Genesis 9", "Skin")
    assert r["node"] == "Genesis 9" and r["material"] == "Skin"
    assert r["shader"] == "DzUberIrayMaterial" and r["property_count"] == 2
    assert r["properties"][0] == {"name": "Diffuse Color", "label": "Base Color",
                                  "type": "color", "value": "#7a7a7a"}


async def test_get_material_missing_zone_lists_available(scene):
    with pytest.raises(ToolError, match="Available: Skin, Lips"):
        await material.daz_get_material("Genesis 9", "Hair")


async def test_set_material_property(scene):
    r = await material.daz_set_material_property("Genesis 9", "Skin", "Diffuse Color", "#3A6EA5")
    assert r == {"node": "Genesis 9", "material": "Skin", "property": "Diffuse Color",
                 "type": "color", "value": "#3a6ea5"}
    with pytest.raises(ToolError, match="Property not found"):
        await material.daz_set_material_property("Genesis 9", "Skin", "Nope", 1)


async def test_set_material_property_bad_color_is_tool_error(scene, monkeypatch):
    def bad(name, value):
        raise ValueError("Color values must be '#RRGGBB'")
    monkeypatch.setattr(scene.nodes["Genesis 9"].mats["Skin"], "set_property_value", bad)
    with pytest.raises(ToolError, match="RRGGBB"):
        await material.daz_set_material_property("Genesis 9", "Skin", "Diffuse Color", "red")


async def test_apply_material_preset_passes_map_paths(scene, tmp_path):
    preset = tmp_path / "p.duf"
    preset.write_text(json.dumps({"image_library": [
        {"filename": "/Runtime/Textures/skin.jpg"}]}), encoding="utf-8")
    r = await material.daz_apply_material_preset("Genesis 9", str(preset))
    node = scene.nodes["Genesis 9"]
    assert node.presets == [(str(preset), ["/Runtime/Textures/skin.jpg"], False)]
    assert r == {"success": True, "node": "Genesis 9", "preset": str(preset),
                 "materials": ["Skin", "Lips"], "material_count": 2}


async def test_convert_to_iray_uber_default_preset(scene):
    r = await material.daz_convert_to_iray_uber("Genesis 9")
    assert r["preset"].endswith("!Iray Uber Base.duf")
    assert r["before"][1] == {"label": "Lips", "shader": "DzDefaultMaterial"}
    assert r["after"][1] == {"label": "Lips", "shader": "DzUberIrayMaterial"}
    assert scene.nodes["Genesis 9"].presets[0][2] is False


async def test_convert_to_iray_uber_no_stock_preset(scene, monkeypatch):
    monkeypatch.setattr(scene, "content_path", lambda rel: None)
    with pytest.raises(ToolError, match="presetPath"):
        await material.daz_convert_to_iray_uber("Genesis 9")


async def test_copy_material(scene):
    r = await material.daz_copy_material("Genesis 9", "Skin", "Clone", "Skin")
    assert r == {"success": True, "source": "Genesis 9/Skin", "destination": "Clone/Skin",
                 "properties_copied": 120, "properties_skipped": 1}
    dst = scene.nodes["Clone"].mats["Skin"]
    assert dst.copied_from is scene.nodes["Genesis 9"].mats["Skin"]
