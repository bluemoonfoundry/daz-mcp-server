"""Unit tests (no Studio) for the wardrobe tools on dazpy: fitting, figure
info, subdivision, dForce simulation and FBX/OBJ export (daz-mcp-server-1kd)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from dazpy import FittedItem, NodeInfo, NumericPropertyWrite, PropertyDetails
from dazpy.exceptions import DazError, NodeNotFoundError, PropertyNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import wardrobe


def _detail(name, label, value, path):
    return PropertyDetails(label, name, "DzFloatProperty", value, 0.0, 1.0, 0.0, path, True)


class FakeNode:
    def __init__(self, scene, label, eid, *, name=None, bones=(), props=None):
        self.scene = scene
        self.label = label
        self.eid = eid
        self.name = name or label.replace(" ", "")
        self.bones = list(bones)
        self.props = dict(props or {})
        self.fitted: list[FittedItem] = []
        self.fit_calls = []
        self.selected = False

    def describe(self):
        return NodeInfo(self.label, self.name, "DzFigure", self.eid, None, 0)

    def fitted_item_info(self):
        return list(self.fitted)

    def fit_to(self, figure):
        self.fit_calls.append(figure.label)
        return "setFollowTarget"

    def unfit(self):
        return {"previous_figure": "Genesis9", "actions": ["cleared follow target"]}

    def bone_names(self):
        return list(self.bones)

    def property_details(self, kind="all"):
        return [_detail(n, n, v, p) for n, (v, p) in self.props.items()]

    def property_detail(self, name):
        if name not in self.props:
            raise PropertyNotFoundError(name)
        v, p = self.props[name]
        return _detail(name, name, v, p)

    def set_numeric_property(self, name, value, **_):
        if name not in self.props:
            raise PropertyNotFoundError(name)
        self.props[name] = (value, self.props[name][1])
        return NumericPropertyWrite(name, name, value)

    def select(self, on=True):
        self.selected = on

    def subdivision(self):
        return {"view": 1, "render": 3} if self.bones else None

    def set_subdivision(self, view, render=None):
        if not self.bones:
            raise PropertyNotFoundError("no SubD")
        return {"previous": {"view": 1, "render": 3}, "current": {"view": view, "render": 3}}


class FakeScene:
    def __init__(self):
        self.nodes = {}
        g9 = FakeNode(self, "Genesis 9", 1, name="Genesis9", bones=["hip", "l_upperarm"],
                      props={"SubDivision Level": (1, "/Mesh Resolution"),
                             "Smile": (0.5, "/Pose Controls/Head/Expressions"),
                             "Height": (0.0, "/Actor/Body"),
                             "XTranslate": (3.0, "/General/Transforms")})
        g9.fitted = [FittedItem("Shirt", "Shirt", "clothing", 5),
                     FittedItem("Hair", "Hair", "hair", 6)]
        self.nodes = {"Genesis 9": g9, "Shirt": FakeNode(self, "Shirt", 5),
                      "Box": FakeNode(self, "Box", 7)}
        self.sim_calls = []
        self.exports = []
        self.select_all_calls = []

    def resolve_node(self, ref):
        for n in self.nodes.values():
            if ref in (n.label, str(n.eid)):
                return n
        raise NodeNotFoundError(f"Node not found: {ref!r}")

    def run_dforce_simulation(self, nodes=None, *, wait=True, **_):
        self.sim_calls.append([n.label for n in nodes] if nodes else None)

    def select_all(self, on=True):
        self.select_all_calls.append(on)

    def export_fbx(self, path, **kw):
        if path.endswith("fail.fbx"):
            raise DazError("DzFbxExporter failed writing")
        self.exports.append(("fbx", path, kw))

    def export_obj(self, path, **kw):
        self.exports.append(("obj", path, kw))


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(wardrobe, "get_scene", lambda: s)
    return s


async def test_list_fitted_items(scene):
    r = await wardrobe.daz_list_fitted_items("Genesis 9")
    assert r == {"figure": "Genesis 9", "fitted_count": 2, "fitted_items": [
        {"label": "Shirt", "name": "Shirt", "type": "clothing", "element_id": 5},
        {"label": "Hair", "name": "Hair", "type": "hair", "element_id": 6}]}


async def test_list_fitted_items_missing_figure(scene):
    with pytest.raises(ToolError, match="Node not found"):
        await wardrobe.daz_list_fitted_items("Ghost")


async def test_fit_and_unfit(scene):
    r = await wardrobe.daz_fit_clothing("Shirt", "Genesis 9")
    assert r == {"success": True, "clothing": "Shirt", "figure": "Genesis 9",
                 "method": "setFollowTarget"}
    assert scene.nodes["Shirt"].fit_calls == ["Genesis 9"]
    r = await wardrobe.daz_unfit_item("Shirt")
    assert r == {"success": True, "item": "Shirt", "previous_figure": "Genesis9",
                 "actions": ["cleared follow target"]}


async def test_unfit_nothing_fitted(scene, monkeypatch):
    monkeypatch.setattr(FakeNode, "unfit", lambda self: {"previous_figure": None, "actions": []})
    r = await wardrobe.daz_unfit_item("Box")
    assert r["actions"] == ["no fitting relationship found"]


async def test_set_subdivision_reports_old_level(scene):
    r = await wardrobe.daz_set_subdivision("Genesis 9", 3)
    assert r == {"success": True, "node": "Genesis 9", "property": "SubDIALevel",
                 "old_level": 1, "new_level": 3, "render_level": 3}
    with pytest.raises(ToolError, match="between 0 and 4"):
        await wardrobe.daz_set_subdivision("Genesis 9", 7)


async def test_set_subdivision_unsupported(scene):
    with pytest.raises(ToolError, match="No subdivision property"):
        await wardrobe.daz_set_subdivision("Box", 1)


async def test_figure_info(scene):
    r = await wardrobe.daz_get_figure_info("Genesis 9")
    assert r["generation"] == "Genesis9" and r["fitted_item_count"] == 2
    assert r["subdivision_level"] == 1
    assert [m["name"] for m in r["active_morphs"]] == ["Smile"]


async def test_run_dforce_simulation(scene):
    r = await wardrobe.daz_run_dforce_simulation("Shirt")
    assert scene.sim_calls == [["Shirt"]] and r["node"] == "Shirt"
    r = await wardrobe.daz_run_dforce_simulation()
    assert scene.sim_calls[-1] is None and r["node"] == "all simulatable nodes"


async def test_export_selected_nodes(scene):
    r = await wardrobe.daz_export_fbx("C:/out/a.fbx", ["Genesis 9", "Shirt"], scale_factor=2.0)
    kind, path, kw = scene.exports[0]
    assert (kind, path, kw["selected_only"]) == ("fbx", "C:/out/a.fbx", True)
    assert kw["options"]["Scale"] == 2.0 and kw["options"]["Morphs"] is True
    assert scene.select_all_calls[0] is False
    assert scene.nodes["Shirt"].selected and r["exported_nodes"] == ["Genesis 9", "Shirt"]


async def test_export_whole_scene_and_errors(scene):
    r = await wardrobe.daz_export_obj("C:/out/a.obj")
    assert scene.exports[0][2]["selected_only"] is False and r["format"] == "Wavefront Object"
    with pytest.raises(ToolError, match="None of the specified nodes"):
        await wardrobe.daz_export_obj("C:/out/b.obj", ["Ghost"])
    with pytest.raises(ToolError, match="failed"):
        await wardrobe.daz_export_fbx("C:/out/fail.fbx")
