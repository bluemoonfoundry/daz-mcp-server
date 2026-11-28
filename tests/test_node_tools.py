"""Unit tests (no Studio) for the node tools on dazpy's resolve_node and
property search: daz_get_node, daz_find_nodes, daz_set_property,
daz_delete_node, daz_set_parent, daz_set_morph, daz_list_morphs and
daz_search_morphs (daz-mcp-server-bzh, -nde)."""
from __future__ import annotations

import pytest
from dazpy import MorphInfo, NodeInfo, NumericPropertyWrite
from dazpy.exceptions import AmbiguousNodeError, NodeNotFoundError, PropertyNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import morph, transform


class FakeNode:
    def __init__(self, scene, info, props=None, morphs=None):
        self.scene = scene
        self.info = info
        self.props = dict(props or {})
        self.morphs = list(morphs or [])
        self.parent_calls = []

    def describe(self):
        return self.info

    def numeric_properties(self, include_modifiers=False):
        assert include_modifiers, "node tools must include the modifier stack"
        return dict(self.props)

    def set_numeric_property(self, name, value, *, substring_fallback=False, unlock=True):
        assert unlock
        for label in self.props:
            if label.lower() == name.lower() or (
                    substring_fallback and name.lower() in label.lower()):
                if label == "Label Text":
                    raise TypeError(f"Property is not numeric: {label!r}")
                self.props[label] = value
                return NumericPropertyWrite(label, label.replace(" ", ""), value)
        raise PropertyNotFoundError(f"Property not found: {name!r}")

    def morph_info(self, pattern=None, include_zero=False):
        return [m for m in self.morphs
                if (include_zero or m.value != 0)
                and (not pattern or pattern.lower() in (m.name + m.label).lower())]

    def delete(self):
        self.scene.deleted.append(self.info.label)
        return True

    def reparent(self, new_parent, *, preserve_world_transform=True):
        self.parent_calls.append(("reparent", new_parent.info.label, preserve_world_transform))

    def unparent(self, *, preserve_world_transform=True):
        self.parent_calls.append(("unparent", preserve_world_transform))


def _info(label, eid, parent=None, children=0, typ="DzNode"):
    return NodeInfo(label, label.replace(" ", ""), typ, eid, parent, children)


class FakeScene:
    def __init__(self):
        self.deleted = []
        self.nodes = {
            "Genesis 9": FakeNode(self, _info("Genesis 9", 10, None, 6, "DzFigure"),
                                  props={"X Translate": 0.0, "Head Size": 1.0, "Label Text": 0},
                                  morphs=[MorphInfo("PHMSmile", "Smile", 0.5, "Morphs/Face"),
                                          MorphInfo("PHMFrown", "Frown", 0.0, "Morphs/Face")]),
            "Sword": FakeNode(self, _info("Sword", 20, "Genesis 9")),
            "Table": FakeNode(self, _info("Table", 30, None, 2)),
        }

    def resolve_node(self, ref):
        ref = str(ref)
        if ref == "Chair":
            raise AmbiguousNodeError("Chair", 2, [_info("Chair", 1), _info("Chair", 2, "Room")])
        if ref.isdigit():
            for n in self.nodes.values():
                if n.info.element_id == int(ref):
                    return n
        if ref in self.nodes:
            return self.nodes[ref]
        raise NodeNotFoundError(f"Node not found: {ref!r}")

    def find_nodes(self, query):
        if query == "Chair":
            return [_info("Chair", 1), _info("Chair", 2, "Room")]
        return [n.info for n in self.nodes.values() if n.info.label == query]


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(transform, "get_scene", lambda: s)
    monkeypatch.setattr(morph, "get_scene", lambda: s)
    return s


async def test_get_node_includes_modifier_properties(scene):
    r = await transform.daz_get_node("Genesis 9")
    assert r == {"name": "Genesis9", "label": "Genesis 9", "type": "DzFigure",
                 "elementID": 10, "parent": None,
                 "properties": {"X Translate": 0.0, "Head Size": 1.0, "Label Text": 0}}


async def test_get_node_by_element_id(scene):
    assert (await transform.daz_get_node("20"))["label"] == "Sword"


async def test_ambiguous_label_lists_element_ids(scene):
    with pytest.raises(ToolError, match="elementID") as exc:
        await transform.daz_get_node("Chair")
    assert "Room" in str(exc.value)


async def test_missing_node_is_tool_error(scene):
    with pytest.raises(ToolError, match="Ghost"):
        await transform.daz_delete_node("Ghost")


async def test_find_nodes(scene):
    r = await transform.daz_find_nodes("Chair")
    assert r["count"] == 2
    assert r["matches"][1] == {"label": "Chair", "name": "Chair", "type": "DzNode",
                               "elementID": 2, "parent": "Room"}


async def test_find_nodes_requires_query(scene):
    with pytest.raises(ToolError, match="query"):
        await transform.daz_find_nodes("")


async def test_set_property(scene):
    r = await transform.daz_set_property("Genesis 9", "head size", 1.2)
    assert r == {"node": "Genesis 9", "elementID": 10, "property": "Head Size", "value": 1.2}


async def test_set_property_missing_and_not_numeric(scene):
    with pytest.raises(ToolError, match="Property not found"):
        await transform.daz_set_property("Genesis 9", "Nope", 1)
    with pytest.raises(ToolError, match="not numeric"):
        await transform.daz_set_property("Genesis 9", "Label Text", 1)


async def test_delete_node(scene):
    r = await transform.daz_delete_node("Table")
    assert r == {"deleted": "Table", "child_count": 2}
    assert scene.deleted == ["Table"]


async def test_set_parent(scene):
    r = await transform.daz_set_parent("Sword", "Table", maintain_world_transform=False)
    assert r == {"success": True, "node": "Sword", "newParent": "Table",
                 "previousParent": "Genesis 9"}
    assert scene.nodes["Sword"].parent_calls == [("reparent", "Table", False)]


async def test_set_parent_scene_unparents(scene):
    r = await transform.daz_set_parent("Sword", "Scene")
    assert r["newParent"] is None and r["previousParent"] == "Genesis 9"
    assert scene.nodes["Sword"].parent_calls == [("unparent", True)]


async def test_set_morph_substring(scene):
    r = await morph.daz_set_morph("Genesis 9", "head", 0.9)
    assert r == {"node": "Genesis 9", "morph": "Head Size", "internal_name": "HeadSize",
                 "value": 0.9}


async def test_set_morph_missing(scene):
    with pytest.raises(ToolError, match="Morph not found"):
        await morph.daz_set_morph("Genesis 9", "tail", 1.0)


async def test_list_and_search_morphs(scene):
    r = await morph.daz_list_morphs("Genesis 9")
    assert r == {"morphs": [{"name": "PHMSmile", "label": "Smile", "value": 0.5,
                             "path": "Morphs/Face"}],
                 "count": 1, "nodeLabel": "Genesis 9"}
    r = await morph.daz_search_morphs("Genesis 9", "frown", include_zero=True)
    assert [m["name"] for m in r["morphs"]] == ["PHMFrown"] and r["pattern"] == "frown"


async def test_list_morphs_missing_node(scene):
    with pytest.raises(ToolError, match="Node not found"):
        await morph.daz_list_morphs("Ghost")
