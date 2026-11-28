"""Unit tests (no Studio) for the keyframe tools on dazpy's frame-based keys
(daz-mcp-server-scz). The old scripts keyed frame N at DzTime tick N, so
"frame 30" landed at frame 0.19; dazpy converts frames to ticks."""
from __future__ import annotations

import pytest
from dazpy import NodeInfo
from dazpy.exceptions import NodeNotFoundError, PropertyNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import animation


class FakeProp:
    def __init__(self):
        self.keys: dict[int, float] = {}

    @property
    def label(self):
        return "X Translate"

    def set_key_at_frame(self, frame, value):
        self.keys[frame] = value
        return value

    def keys_by_frame(self):
        return sorted((float(f), v) for f, v in self.keys.items())

    def remove_key_at_frame(self, frame):
        return self.keys.pop(frame, None) is not None

    def clear_keys(self):
        n = len(self.keys)
        self.keys.clear()
        return n


class FakeNode:
    def __init__(self):
        self.prop = FakeProp()

    def describe(self):
        return NodeInfo("Genesis 9", "Genesis9", "DzFigure", 1, None, 0)

    def find_numeric_property(self, name):
        if name.lower() not in ("xtranslate", "x translate"):
            raise PropertyNotFoundError(f"Numeric property not found: {name!r}")
        return self.prop


class FakeScene:
    def __init__(self):
        self.node = FakeNode()

    def resolve_node(self, ref):
        if ref != "Genesis 9":
            raise NodeNotFoundError(f"Node not found: {ref!r}")
        return self.node


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(animation, "get_scene", lambda: s)
    return s


async def test_set_and_get_keyframes(scene):
    r = await animation.daz_set_keyframe("Genesis 9", "XTranslate", 30, 100.0)
    assert r == {"success": True, "node": "Genesis 9", "property": "X Translate",
                 "frame": 30, "value": 100.0}
    await animation.daz_set_keyframe("Genesis 9", "XTranslate", 0, 0.0)
    r = await animation.daz_get_keyframes("Genesis 9", "XTranslate")
    assert r == {"keyframes": [{"frame": 0, "value": 0.0}, {"frame": 30, "value": 100.0}],
                 "count": 2}


async def test_fractional_frames_are_kept(scene):
    scene.node.prop.keys = {1.5: 2.0}
    r = await animation.daz_get_keyframes("Genesis 9", "XTranslate")
    assert r["keyframes"] == [{"frame": 1.5, "value": 2.0}]


async def test_remove_keyframe(scene):
    await animation.daz_set_keyframe("Genesis 9", "XTranslate", 30, 1.0)
    r = await animation.daz_remove_keyframe("Genesis 9", "XTranslate", 30)
    assert r == {"success": True, "node": "Genesis 9", "property": "X Translate",
                 "frame": 30, "removed": True}
    r = await animation.daz_remove_keyframe("Genesis 9", "XTranslate", 30)
    assert r["removed"] is False


async def test_clear_animation(scene):
    await animation.daz_set_keyframe("Genesis 9", "XTranslate", 1, 1.0)
    await animation.daz_set_keyframe("Genesis 9", "XTranslate", 2, 2.0)
    r = await animation.daz_clear_animation("Genesis 9", "XTranslate")
    assert r == {"success": True, "node": "Genesis 9", "property": "X Translate", "removed": 2}


async def test_missing_property_and_node(scene):
    with pytest.raises(ToolError, match="Property not found"):
        await animation.daz_set_keyframe("Genesis 9", "Nope", 0, 1.0)
    with pytest.raises(ToolError, match="Node not found"):
        await animation.daz_get_keyframes("Ghost", "XTranslate")
