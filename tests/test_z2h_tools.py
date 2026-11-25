"""Unit tests (no Studio) for the content, asset, Morph Loader Pro and
strand-hair tools on dazpy (daz-mcp-server-z2h, -9o5)."""
from __future__ import annotations

import pytest
from dazpy import ContentCategory, ContentFile, MorphLoadResult, NodeInfo
from dazpy.exceptions import DazError, NodeNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server import _ui_automation
from daz_mcp_server.tools import content, hair, morph


class FakeNode:
    def __init__(self, label):
        self.label = label
        self.calls = []

    def describe(self):
        return NodeInfo(self.label, self.label, "DzFigure", 1, None, 0)

    def save_support_asset(self, path, **kw):
        self.calls.append(("asset", path, kw))
        if not path.startswith("D:/Lib"):
            raise ValueError("output_path must be inside a configured content directory: D:/Lib")
        return "D:/Lib"

    def load_morph(self, obj_path, *, control_node=None, **options):
        self.calls.append(("morph", obj_path, control_node, options))
        if options.get("load_mode") == "Bogus":
            raise DazError("Morph Loader Pro: Unknown loadMode: Bogus")
        return MorphLoadResult(options.get("morph_name", "Morph"),
                               "Smile" if "control_property_name" in options else None, "")


class FakeScene:
    def __init__(self):
        self.nodes = {"Genesis 9": FakeNode("Genesis 9"), "Ctl": FakeNode("Ctl")}

    def resolve_node(self, ref):
        if ref not in self.nodes:
            raise NodeNotFoundError(f"Node not found: {ref!r}")
        return self.nodes[ref]

    def content_categories(self, parent):
        return [ContentCategory("Poses", f"{parent.strip('/')}/Poses".strip("/"), 4)]

    def content_files(self, category):
        return [ContentFile("Hero", "Hero.duf", "D:/Lib/People/Hero.duf")]

    def strand_hair_nodes(self):
        return [{"label": "Hair", "name": "Hair", "element_id": 9, "target": "Genesis 9",
                 "has_geometry": True, "materials": ["Hair"]}]


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    for mod in (content, hair, morph):
        monkeypatch.setattr(mod, "get_scene", lambda: s)
    return s


async def test_list_and_browse_categories(scene):
    r = await content.daz_list_categories("People")
    assert r == {"parent": "People", "count": 1,
                 "categories": [{"name": "Poses", "path": "People/Poses", "duf_count": 4}]}
    r = await content.daz_browse_category("People")
    assert r["items"][0] == {"name": "Hero", "filename": "Hero.duf",
                             "full_path": "D:/Lib/People/Hero.duf"}


async def test_save_prop_asset(scene):
    r = await content.daz_save_prop_asset("Genesis 9", "D:/Lib/Props/x.duf", vendor_name="Me",
                                          smart_parent=True)
    _, _path, kw = scene.nodes["Genesis 9"].calls[0]
    assert kw["vendor"] == "Me" and kw["smart_parent"] is True and kw["write_uvs"] is None
    assert r["baseDataPath"] == "D:/Lib" and r["itemName"] == "Genesis 9"
    with pytest.raises(ToolError, match="content directory"):
        await content.daz_save_prop_asset("Genesis 9", "C:/elsewhere/x.duf")


async def test_load_morph_pro_options_and_control_gating(scene):
    r = await morph.daz_load_morph_pro("Genesis 9", "C:/m.obj", morph_name="Flex",
                                       subdivision=True, control_property_name="Smile")
    _, _obj, control, opts = scene.nodes["Genesis 9"].calls[0]
    assert opts["subdivision"] is True and "control_property_name" not in opts
    assert control is None and r["morphName"] == "Flex" and r["controlProperty"] is None
    await morph.daz_load_morph_pro("Genesis 9", "C:/m.obj", create_control_property=True,
                                   control_node_label="Ctl", control_property_name="Smile",
                                   control_property_erc_type="ERCDeltaAdd")
    _, _, control, opts = scene.nodes["Genesis 9"].calls[1]
    assert control is scene.nodes["Ctl"] and opts["control_property_erc_type"] == "ERCDeltaAdd"
    with pytest.raises(ToolError, match="Unknown loadMode"):
        await morph.daz_load_morph_pro("Genesis 9", "C:/m.obj", load_mode="Bogus")
    with pytest.raises(ToolError, match="control_property_name is required"):
        await morph.daz_load_morph_pro("Genesis 9", "C:/m.obj", create_control_property=True)


async def test_list_strand_hair_nodes(scene):
    r = await hair.daz_list_strand_hair_nodes()
    assert r["count"] == 1 and r["nodes"][0]["target"] == "Genesis 9"


async def test_create_strand_hair_auto_confirm(monkeypatch):
    calls = []

    async def submit(script_id, args):
        calls.append(("submit", script_id, args))
        return {"request_id": "script-1", "status": "queued"}

    async def wait(request_id, poll_interval_seconds, timeout_seconds):
        calls.append(("wait", request_id))
        return {"status": "completed", "result": {"node": "Strand-Based Hair"}}

    monkeypatch.setattr(hair, "_execute_by_id_async", submit)
    monkeypatch.setattr(hair, "daz_wait_for_request", wait)
    monkeypatch.setattr(_ui_automation, "_require_pywinauto", lambda: None)
    monkeypatch.setattr(_ui_automation, "drive_strand_hair_create",
                        lambda timeout: calls.append(("click", timeout)))
    r = await hair.daz_create_strand_hair("Genesis 9", auto_confirm=True, dialog_timeout=5)
    assert [c[0] for c in calls] == ["submit", "click", "wait"]
    assert r["result"]["node"] == "Strand-Based Hair"
    calls.clear()
    r = await hair.daz_create_strand_hair("Genesis 9")
    assert [c[0] for c in calls] == ["submit"] and r["request_id"] == "script-1"
