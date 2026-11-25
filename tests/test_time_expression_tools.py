"""Unit tests (no Studio) for daz_time_expression / daz_sync_character_beats on
dazpy frame-based keys (daz-mcp-server-ord, onf)."""
from __future__ import annotations

import pytest
from dazpy import NodeInfo, NumericCandidateMatch
from dazpy.exceptions import NodeNotFoundError

from daz_mcp_server.tools import cinematic


class FakeSkel:
    def __init__(self, label, bones, dials):
        self.label, self.bones, self.dials = label, bones, set(dials)
        self.keyed: list = []
        self.bone_keys: dict = {}

    def describe(self):
        return NodeInfo(self.label, self.label, "DzFigure", 1, None, 0)

    def bone_names(self):
        return list(self.bones)

    def key_numeric_candidates(self, slots):
        out = []
        for names, keys in slots:
            hit = next((n for n in names if n in self.dials), None)
            if hit:
                self.keyed.append((hit, list(keys)))
            out.append(NumericCandidateMatch(tuple(names), keys[-1][1] if keys else 0.0, hit,
                                             "property" if hit else None, None))
        return out

    def key_bone_axes(self, data):
        self.bone_keys.update(data)
        return [b for b in data if b not in self.bones]


class FakeScene:
    def __init__(self):
        self.nodes = {
            "Alice": FakeSkel("Alice", ["hip", "spine4"], ["facs_ctrl_Happy", "facs_ctrl_Sad"]),
            "Bob": FakeSkel("Bob", ["hip", "chestUpper"], ["eCTRLMouthSmile"]),
        }

    def resolve_node(self, ref):
        if ref not in self.nodes:
            raise NodeNotFoundError(f"Node not found: {ref!r}")
        return self.nodes[ref]


@pytest.fixture()
def scene(monkeypatch):
    s = FakeScene()
    monkeypatch.setattr(cinematic, "get_scene", lambda: s)
    return s


async def test_time_expression_keys_face_controller_and_g9_chest(scene):
    r = await cinematic.daz_time_expression("Alice", "happy", peak_frame=20, ease_in_frames=10,
                                            hold_frames=5, ease_out_frames=5, intensity=0.5)
    alice = scene.nodes["Alice"]
    assert alice.keyed == [("facs_ctrl_Happy", [(10, 0.0), (20, 0.5), (25, 0.5), (30, 0.0)])]
    assert alice.bone_keys == {"spine4": {"x": [(10, 0.0), (20, 1.5), (25, 1.5), (30, 0.0)]}}
    assert r["appliedMorphs"] == [{"morph": "facs_ctrl_Happy", "peakValue": 0.5}]
    assert r["bodyAdjustments"] == [{"bone": "spine4", "property": "XRotate", "peakValue": 1.5}]
    assert r["keyframesSet"] == 8 and r["durationFrames"] == 20 and r["holdFrames"] == 5


async def test_time_expression_baseline_and_feature_fallback(scene):
    r = await cinematic.daz_time_expression("Bob", "loving", peak_frame=10, ease_in_frames=0,
                                            hold_frames=0, ease_out_frames=0, intensity=1.0,
                                            baseline_frame=None)
    bob = scene.nodes["Bob"]
    assert bob.keyed[0] == ("eCTRLMouthSmile", [(10, 0.6)])
    assert r["notFound"] == ["facs_ctrl_EyeSquint"]
    assert bob.bone_keys == {"chestUpper": {"x": [(10, 2.0)]}}


async def test_time_expression_missing_character(scene):
    from fastmcp.exceptions import ToolError
    with pytest.raises(ToolError, match="Node not found"):
        await cinematic.daz_time_expression("Ghost", "happy", peak_frame=10)


async def test_sync_beats_reports_per_character(scene):
    r = await cinematic.daz_sync_character_beats(
        beat_frame=30,
        characters=[{"label": "Alice", "emotion": "sad"}, {"label": "Ghost", "emotion": "happy"}])
    by = {x["character"]: x for x in r["results"]}
    assert by["Alice"]["status"] == "ok" and by["Ghost"]["status"] == "error"
    assert r["totalKeyframes"] == by["Alice"]["detail"]["keyframesSet"] > 0
