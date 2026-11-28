"""Tests for the scene-recipe tools (thin wrappers over dazpy.recipe)."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from dazpy.exceptions import RecipeNotAppliedError

from daz_mcp_server.tools import recipe
from test_workflow_profile import _profile_snapshot

RECIPE_TOOLS = {
    "daz_recipe_validate",
    "daz_recipe_plan",
    "daz_recipe_apply",
    "daz_recipe_observe",
    "daz_recipe_render",
}


class _Result:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return self._payload


@pytest.fixture(autouse=True)
def _scene(monkeypatch):
    monkeypatch.setattr(recipe, "get_scene", lambda: "SCENE")


async def test_apply_passes_policy_and_resolutions(monkeypatch):
    calls = []

    def fake_apply(rec, scene, *, on_conflict, resolutions):
        calls.append((rec, scene, on_conflict, resolutions))
        return _Result({"applied": True})

    monkeypatch.setattr(recipe.dz_recipe, "apply", fake_apply)
    out = await recipe.daz_recipe_apply(
        {"id": "x"}, "recipe_wins", {"actors.a.pose": "scene"}
    )
    assert out == {"applied": True}
    assert calls == [({"id": "x"}, "SCENE", "recipe_wins", {"actors.a.pose": "scene"})]


async def test_plan_passes_policy_and_resolutions(monkeypatch):
    calls = []

    def fake_plan(rec, scene, *, on_conflict, resolutions):
        calls.append((on_conflict, resolutions))
        return _Result({"steps": []})

    monkeypatch.setattr(recipe.dz_recipe, "plan", fake_plan)
    assert await recipe.daz_recipe_plan({"id": "x"}) == {"steps": []}
    assert calls == [("ask", None)]


async def test_validate_returns_report(monkeypatch):
    monkeypatch.setattr(
        recipe.dz_recipe, "validate", lambda rec, scene=None: _Result({"ok": True})
    )
    assert await recipe.daz_recipe_validate({"id": "x"}) == {"ok": True}


async def test_validate_error_returned_as_data_not_toolerror():
    out = await recipe.daz_recipe_apply({"recipe_version": 1})
    assert out["ok"] is False
    assert out["errors"][0]["code"] == "missing_field"


async def test_invalid_policy_returned_as_data(monkeypatch):
    def boom(*a, **k):
        raise ValueError("bad on_conflict 'nope'")

    monkeypatch.setattr(recipe.dz_recipe, "plan", boom)
    out = await recipe.daz_recipe_plan({"id": "x"}, "nope")
    assert out == {"ok": False, "error": "bad on_conflict 'nope'"}


async def test_observe(monkeypatch):
    monkeypatch.setattr(
        recipe.dz_recipe, "observe", lambda rec, scene: _Result({"in_sync": True})
    )
    assert await recipe.daz_recipe_observe({"id": "x"}) == {"in_sync": True}


async def test_render_returns_shots(monkeypatch):
    calls = []

    def fake_render(rec, scene, *, shots, force):
        calls.append((shots, force))
        return [_Result({"id": "a"}), _Result({"id": "b"})]

    monkeypatch.setattr(recipe.dz_recipe, "render", fake_render)
    out = await recipe.daz_recipe_render({"id": "x"}, ["a", "b"], True)
    assert out == {"shots": [{"id": "a"}, {"id": "b"}]}
    assert calls == [(["a", "b"], True)]


async def test_render_not_applied_returns_reason(monkeypatch):
    def fake_render(rec, scene, *, shots, force):
        raise RecipeNotAppliedError("apply first", _Result({"applied": False}))

    monkeypatch.setattr(recipe.dz_recipe, "render", fake_render)
    out = await recipe.daz_recipe_render({"id": "x"})
    assert out == {"ok": False, "reason": "apply first", "observe": {"applied": False}}


async def test_render_unknown_shot_returned_as_data(monkeypatch):
    def fake_render(rec, scene, *, shots, force):
        raise ValueError("unknown shot id(s): z")

    monkeypatch.setattr(recipe.dz_recipe, "render", fake_render)
    out = await recipe.daz_recipe_render({"id": "x"}, ["z"])
    assert out == {"ok": False, "error": "unknown shot id(s): z"}


def test_schema_resource_serves_v1_and_v2():
    v1 = json.loads(recipe.daz_recipe_schema_version_resource("1"))
    v2 = json.loads(recipe.daz_recipe_schema_version_resource("2"))
    assert v2 != v1
    assert v2["properties"]["recipe_version"] == {"const": 2}
    # the unversioned resource serves the current (latest) version
    assert json.loads(recipe.daz_recipe_schema_resource()) == v2


def test_schema_resource_unsupported_version_is_clear():
    with pytest.raises(ValueError, match="unsupported recipe schema version"):
        recipe.daz_recipe_schema_version_resource("3")


async def test_validate_tool_accepts_v2_recipe(monkeypatch):
    v2 = {
        "recipe_version": 2,
        "id": "x",
        "actors": {
            "abby": {
                "node": "Abby",
                "presets": [{"find": "Young Shape"}],
                "wearing": [{"add": {"sku": "12345"}, "key": "outfit"}],
            }
        },
    }
    seen = []

    def fake_validate(rec, scene=None):
        seen.append((rec, scene))
        return _Result({"ok": True})

    monkeypatch.setattr(recipe.dz_recipe, "validate", fake_validate)
    assert await recipe.daz_recipe_validate(v2) == {"ok": True}
    assert seen == [(v2, "SCENE")]


@pytest.mark.parametrize(
    "tool", [recipe.daz_recipe_validate, recipe.daz_recipe_plan, recipe.daz_recipe_apply]
)
def test_tool_docs_describe_v2(tool):
    doc = tool.__doc__
    for word in ("recipe_version", "find", "node", "presets", "wearing", "add",
                 "replace", "with", "remove", "key", "if_missing", "ignore"):
        assert word in doc, word


def test_compact_profile_includes_recipe_tools():
    assert RECIPE_TOOLS <= set(_profile_snapshot("compact")["tools"])


def test_schema_resource_available_in_compact():
    snap = _profile_snapshot("compact")
    assert "daz://recipe/schema" in snap["resources"]
    assert "daz://recipe/schema/{version}" in snap["templates"]
