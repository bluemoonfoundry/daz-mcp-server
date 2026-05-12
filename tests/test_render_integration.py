"""Integration tests — render settings and render quality.

Tools covered (settings, non-blocking)
---------------------------------------
- daz_get_render_settings
- daz_set_render_quality

Slow tests (actual renders — require @pytest.mark.slow)
-------------------------------------------------------
- daz_render
- daz_render_with_camera

Run slow tests explicitly:
    uv run pytest tests/test_render_integration.py -m slow -v
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_get_render_settings,
    daz_render,
    daz_render_with_camera,
    daz_set_render_quality,
)


# ---------------------------------------------------------------------------
# daz_get_render_settings
# ---------------------------------------------------------------------------

class TestGetRenderSettings:
    async def test_returns_dict(self, live_client):
        result = await daz_get_render_settings()
        assert isinstance(result, dict)

    async def test_has_render_engine(self, live_client):
        result = await daz_get_render_settings()
        text = str(result).lower()
        assert any(k in text for k in ["engine", "render", "iray", "3delight", "quality"])

    async def test_has_dimensions(self, live_client):
        result = await daz_get_render_settings()
        text = str(result).lower()
        assert any(k in text for k in ["width", "height", "size", "resolution"])


# ---------------------------------------------------------------------------
# daz_set_render_quality
# ---------------------------------------------------------------------------

class TestSetRenderQuality:
    @pytest.mark.parametrize("preset", ["draft", "preview", "good", "final"])
    async def test_quality_presets(self, live_client, preset):
        result = await daz_set_render_quality(preset)
        assert isinstance(result, dict)

    async def test_invalid_preset_raises(self, live_client):
        with pytest.raises((ToolError, ValueError, Exception)):
            await daz_set_render_quality("nonexistent_preset_xyz")


# ---------------------------------------------------------------------------
# Slow render tests — skipped by default, run with -m slow
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.integration
class TestRender:
    async def test_render_to_temp_path(self, live_client, tmp_path):
        output = str(tmp_path / "test_render.png").replace("\\", "/")
        result = await daz_render(output_path=output)
        assert isinstance(result, dict)
        assert result.get("success") or "render" in str(result).lower()


@pytest.mark.slow
@pytest.mark.integration
class TestRenderWithCamera:
    async def test_render_from_temp_camera(self, live_client, temp_camera, tmp_path):
        output = str(tmp_path / "cam_render.png").replace("\\", "/")
        result = await daz_render_with_camera(temp_camera, output_path=output)
        assert isinstance(result, dict)
