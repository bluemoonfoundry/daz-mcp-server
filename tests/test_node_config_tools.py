"""Unit tests (no Studio) for daz_export_node_config / daz_import_node_config on
dazpy (daz-mcp-server-ord, node-config slice)."""
from __future__ import annotations

import json

import pytest
from dazpy import BatchPropertyResult, CameraInfo, LightInfo, NodeInfo, PropertyDetails
from dazpy.exceptions import NodeNotFoundError

from daz_mcp_server.tools import cinematic


def _p(name, value):
    return PropertyDetails(name, name, "DzFloatProperty", value, None, None, 0.0, "", True)


class FakeNode:
    def __init__(self, label, eid, typ, props):
        self.label, self.eid, self.typ, self.props = label, eid, typ, props

    def describe(self):
        return NodeInfo(self.label, self.label, self.typ, self.eid, None, 0)

    def property_details(self, kind="all"):
        assert kind == "numeric"
        return [_p(n, v) for n, v in self.props.items()]


class FakeScene:
    def __init__(self):
        self.nodes = {
            "Genesis 9": FakeNode("Genesis 9", 1, "DzFigure",
                                  {"XTranslate": 5.0, "Scale": 1.0, "Smile": 0.4, "Frown": 0.0}),
            "Key": FakeNode("Key", 2, "DzSpotLight", {"XTranslate": 0.0, "Flux": 1500.0}),
            "Camera 1": FakeNode("Camera 1", 3, "DzBasicCamera", {"FocalLength": 65.0}),
        }
        self.batches = []

    def resolve_node(self, ref):
        for n in self.nodes.values():
            if ref in (n.label, str(n.eid)):
                return n
        raise NodeNotFoundError(ref)

    def skeletons(self):
        return [self.nodes["Genesis 9"]]

    def camera_info(self):
        return [CameraInfo(0, "Camera 1", "Camera 1", "DzBasicCamera", 3, (0, 0, 0), 65.0)]

    def light_info(self):
        return [LightInfo(0, "Key", "Key", "DzSpotLight", 2, (0, 0, 0), 1500.0, True)]

    def set_numeric_properties(self, ops):
        self.batches.append(list(ops))
        out = []
        for node, prop, value in ops:
            if node == "Ghost":
                out.append(BatchPropertyResult(False, None, error="Node not found: Ghost"))
            elif prop == "Bogus":
                out.append(BatchPropertyResult(False, None, error="Property not found: Bogus"))
            else:
                out.append(BatchPropertyResult(True, node, prop, value))
        return out


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(cinematic, "get_scene", lambda: s)
    monkeypatch.setattr(cinematic, "_skeleton_nodes", lambda sc: sc.skeletons())
    return s


async def test_export_all_nodes(scene, tmp_path):
    out = tmp_path / "cfg.json"
    r = await cinematic.daz_export_node_config(str(out))
    data = json.loads(out.read_text(encoding="utf-8"))
    g9 = data["nodes"]["Genesis 9"]
    assert g9 == {"_type": "DzFigure", "XTranslate": 5.0, "Scale": 1.0, "Smile": 0.4}
    assert data["nodes"]["Key"] == {"_type": "DzSpotLight", "XTranslate": 0.0, "Flux": 1500.0}
    assert data["nodes"]["Camera 1"]["FocalLength"] == 65.0
    assert r["nodeCount"] == 3 and r["morphCount"] == 1


async def test_export_transforms_only(scene, tmp_path):
    out = tmp_path / "cfg.json"
    await cinematic.daz_export_node_config(str(out), ["Genesis 9"], ["transforms"])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["nodes"] == {"Genesis 9": {"_type": "DzFigure", "XTranslate": 5.0, "Scale": 1.0}}


async def test_import_one_batch_with_status(scene, tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"nodes": {
        "Genesis 9": {"_type": "DzFigure", "XTranslate": 10.0, "Bogus": 1},
        "Key": {"Flux": 900.0},
        "Ghost": {"XTranslate": 1.0}}}), encoding="utf-8")
    r = await cinematic.daz_import_node_config(str(cfg), scale_transforms=2.0)
    assert len(scene.batches) == 1
    assert ("Genesis 9", "XTranslate", 20.0) in scene.batches[0]
    by_node = {x["node"]: x for x in r["results"]}
    assert by_node["Genesis 9"]["status"] == "partial"
    assert by_node["Genesis 9"]["failed"] == [{"property": "Bogus",
                                               "error": "Property not found: Bogus"}]
    assert by_node["Key"]["status"] == "ok" and by_node["Ghost"]["status"] == "skipped"
    assert (r["successCount"], r["failureCount"], r["skippedCount"]) == (2, 0, 1)


async def test_import_missing_node_is_error_without_skip(scene, tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"Ghost": {"XTranslate": 1.0}}), encoding="utf-8")
    r = await cinematic.daz_import_node_config(str(cfg), skip_missing=False)
    assert r["results"][0]["status"] == "error" and r["failureCount"] == 1
