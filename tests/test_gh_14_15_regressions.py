"""Regression tests for GitHub issues #14 and #15 (reported by @qhuy729).

#14: daz_get_figure_info called ``getElementID()``, which is not a method in
     DazScript -- ``elementID`` is a property.
#15: daz_get_animation_info compared the raw ``Scene.getTimeStep()`` result
     (a DzTime object, serialised as a dict) to an int.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from vangard_daz_mcp._registry import _REGISTRY
from vangard_daz_mcp.tools import animation


def test_figure_info_script_uses_element_id_property():
    script = _REGISTRY["vangard-get-figure-info"][1]
    assert "getElementID" not in script
    assert "fig.elementID" in script


def test_no_registered_script_calls_get_element_id():
    offenders = [sid for sid, entry in _REGISTRY.items() if "getElementID" in entry[1]]
    assert offenders == []


class _FakeScene:
    def frame(self):
        return 5

    def anim_range(self):
        return {"start": 0, "end": 29}


class _FakeClient:
    def __init__(self, value):
        self.value = value
        self.scripts: list[str] = []

    def execute(self, script):
        self.scripts.append(script)
        return SimpleNamespace(value=self.value)


def _patch(monkeypatch, value):
    client = _FakeClient(value)
    monkeypatch.setattr(animation, "get_scene", lambda: _FakeScene())
    monkeypatch.setattr(animation, "get_daz_client", lambda: client)
    return client


@pytest.mark.asyncio
async def test_animation_info_requests_numeric_time_step(monkeypatch):
    client = _patch(monkeypatch, 200)  # 4800 / 200 = 24 fps
    result = await animation.daz_get_animation_info()
    assert "getTimeStep().valueOf()" in client.scripts[0]
    assert result["fps"] == 24
    assert result["totalFrames"] == 30
    assert result["durationSeconds"] == 1.25


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", [{"valueOf": {}}, None, 0, -1, "160", True])
async def test_animation_info_falls_back_on_non_numeric_step(monkeypatch, bad):
    _patch(monkeypatch, bad)
    result = await animation.daz_get_animation_info()
    assert result["fps"] == 30
