"""Unit tests (no Studio) for the dForce and Transfer Utility tools on dazpy
(daz-mcp-server-1kd part 2)."""
from __future__ import annotations

import pytest
from dazpy import NodeInfo
from dazpy.exceptions import DazError, NodeNotFoundError, PropertyNotFoundError
from fastmcp.exceptions import ToolError

from daz_mcp_server.tools import wardrobe


class FakeNode:
    def __init__(self, label, eid, *, has_dforce=True):
        self.label = label
        self.eid = eid
        self.has_dforce = has_dforce
        self.weights = None
        self.frozen = None
        self.calls = []

    def describe(self):
        return NodeInfo(self.label, self.label, "DzFigure", self.eid, None, 0)

    def _need(self):
        if not self.has_dforce:
            raise DazError("No dForce modifier on 'Box' (add one with add_dforce_dynamic_surface)")

    def add_dforce_dynamic_surface(self):
        added = not self.has_dforce
        self.has_dforce = True
        return added

    def dforce_influence_weights(self):
        self._need()
        return self.weights

    def set_dforce_influence_weights(self, default=1.0, overrides=None):
        self._need()
        self.calls.append(("weights", default, dict(overrides or {})))
        return 280, len(overrides or {})

    def set_dforce_property(self, name, value):
        self._need()
        if name == "Nope":
            raise PropertyNotFoundError("dForce property 'Nope' not found. Available: A, B")
        return {"modifier": "DzDForceModifier", "property": name, "old_value": 1.0,
                "new_value": value}

    def dforce_surface_properties(self, material=None):
        self._need()
        return material or "Cloth", [{"name": "Friction", "label": "Friction",
                                       "type": "numeric", "value": 0.2}]

    def set_dforce_surface_property(self, name, value, material=None):
        self._need()
        return {"material": material or "Cloth", "property": name, "old_value": 0.2,
                "new_value": value}

    def freeze_dforce(self, on=True):
        self.frozen = on
        return 1 if self.has_dforce else 0


class FakeScene:
    def __init__(self):
        self.nodes = {"Dress": FakeNode("Dress", 1), "Box": FakeNode("Box", 2, has_dforce=False),
                      "Genesis 9": FakeNode("Genesis 9", 3)}
        self.transfers = []

    def resolve_node(self, ref):
        if ref not in self.nodes:
            raise NodeNotFoundError(f"Node not found: {ref!r}")
        return self.nodes[ref]

    def freeze_dforce(self, on=True):
        return sum(1 for n in self.nodes.values() if n.has_dforce)

    def transfer_utility(self, source, target, **flags):
        if target.label == "Box":
            raise DazError("Transfer Utility: doTransfer() returned false")
        self.transfers.append((source.label, target.label, flags))


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(wardrobe, "get_scene", lambda: s)
    return s


async def test_add_dynamic_surface(scene):
    r = await wardrobe.daz_add_dforce_dynamic_surface("Box")
    assert r == {"success": True, "node": "Box", "already_present": False,
                 "modifier": "DzDForceModifier"}
    r = await wardrobe.daz_add_dforce_dynamic_surface("Box")
    assert r["already_present"] is True


async def test_influence_weights(scene):
    r = await wardrobe.daz_set_dforce_influence_weights("Dress", {0: 0.0, 5: 0.0}, 1.0)
    assert scene.nodes["Dress"].calls == [("weights", 1.0, {0: 0.0, 5: 0.0})]
    assert r == {"success": True, "node": "Dress", "vertex_count": 280, "default_weight": 1.0,
                 "overridden_count": 2}
    r = await wardrobe.daz_get_dforce_influence_weights("Dress")
    assert r == {"success": True, "node": "Dress", "has_influence_weights": False, "weights": []}
    scene.nodes["Dress"].weights = [1.0, 0.0]
    r = await wardrobe.daz_get_dforce_influence_weights("Dress")
    assert r["has_influence_weights"] is True and r["vertex_count"] == 2


async def test_no_dforce_modifier_is_tool_error(scene):
    with pytest.raises(ToolError, match="No dForce modifier"):
        await wardrobe.daz_get_dforce_influence_weights("Box")


async def test_set_dforce_property(scene):
    r = await wardrobe.daz_set_dforce_property("Dress", "Dynamics Strength", 0.5)
    assert r == {"success": True, "node": "Dress", "modifier": "DzDForceModifier",
                 "property": "Dynamics Strength", "old_value": 1.0, "new_value": 0.5}
    with pytest.raises(ToolError, match="Available: A, B"):
        await wardrobe.daz_set_dforce_property("Dress", "Nope", 1)


async def test_surface_properties(scene):
    r = await wardrobe.daz_get_dforce_surface_properties("Dress")
    assert r == {"node": "Dress", "material": "Cloth", "property_count": 1,
                 "properties": [{"name": "Friction", "label": "Friction", "type": "numeric",
                                 "value": 0.2}]}
    r = await wardrobe.daz_set_dforce_surface_property("Dress", "Friction", 0.4, "Skirt")
    assert r == {"success": True, "node": "Dress", "material": "Skirt", "property": "Friction",
                 "old_value": 0.2, "new_value": 0.4}


async def test_bake_freezes_dforce(scene):
    r = await wardrobe.daz_bake_simulation("Dress")
    assert scene.nodes["Dress"].frozen is True
    assert r == {"success": True, "node": "Dress", "method": "freeze", "modifiers_frozen": 1}
    with pytest.raises(ToolError, match="No dForce modifier"):
        await wardrobe.daz_bake_simulation("Box")


async def test_bake_all(scene):
    r = await wardrobe.daz_bake_simulation()
    assert r["node"] == "all" and r["modifiers_frozen"] == 2


async def test_transfer_utility(scene):
    r = await wardrobe.daz_run_transfer_utility("Genesis 9", "Dress", transfer_uvs=True)
    src, dst, flags = scene.transfers[0]
    assert (src, dst) == ("Genesis 9", "Dress")
    assert flags["binding"] and flags["morphs"] and flags["uvs"] and flags["fit_to_figure"]
    assert not flags["merge_hierarchies"]
    assert r == {"success": True, "source": "Genesis 9", "target": "Dress"}
    with pytest.raises(ToolError, match="doTransfer"):
        await wardrobe.daz_run_transfer_utility("Genesis 9", "Box")
