"""Integration tests — lighting presets, animation, and atmosphere.

Tools covered
-------------
- daz_apply_lighting_preset
- daz_animate_light
- daz_create_light_sequence
- daz_set_scene_atmosphere
- daz_apply_visual_style

Note: daz_list_lights / daz_create_light / daz_delete_node are covered in
test_phase5_integration.py and used here only as helpers.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_animate_light,
    daz_apply_lighting_preset,
    daz_apply_visual_style,
    daz_clear_animation,
    daz_create_light_sequence,
    daz_delete_node,
    daz_list_lights,
    daz_set_scene_atmosphere,
)


# ---------------------------------------------------------------------------
# Helper: track lights created during a test so they can be cleaned up
# ---------------------------------------------------------------------------

async def _delete_lights_created_after(lights_before: list) -> None:
    """Delete any lights that appeared in the scene after a baseline snapshot."""
    lights_after = await daz_list_lights()
    before_labels = {lt.get("label") for lt in lights_before}
    for lt in lights_after.get("lights", []):
        if lt.get("label") not in before_labels:
            try:
                await daz_delete_node(lt["label"])
            except Exception:
                pass


# ---------------------------------------------------------------------------
# daz_apply_lighting_preset
# ---------------------------------------------------------------------------

class TestApplyLightingPreset:
    @pytest.mark.parametrize("preset", [
        "three-point", "rembrandt", "butterfly", "split",
    ])
    async def test_preset_creates_lights(self, live_client, figure_label, preset):
        before = await daz_list_lights()
        result = await daz_apply_lighting_preset(preset, subject_label=figure_label)
        assert isinstance(result, dict)
        await _delete_lights_created_after(before.get("lights", []))

    async def test_preset_without_subject(self, live_client):
        before = await daz_list_lights()
        result = await daz_apply_lighting_preset("three-point")
        assert isinstance(result, dict)
        await _delete_lights_created_after(before.get("lights", []))

    async def test_invalid_preset_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_apply_lighting_preset("nonexistent-preset-xyz")


# ---------------------------------------------------------------------------
# daz_animate_light
# ---------------------------------------------------------------------------

class TestAnimateLight:
    @pytest.mark.parametrize("movement", ["flicker", "pulse", "fade-out"])
    async def test_movement_types(self, live_client, temp_spot_light, movement):
        result = await daz_animate_light(
            temp_spot_light, movement_type=movement, end_frame=30
        )
        assert isinstance(result, dict)
        # Clean up keyframes
        try:
            await daz_clear_animation(temp_spot_light, "Flux")
        except Exception:
            pass

    async def test_strobe(self, live_client, temp_spot_light):
        result = await daz_animate_light(
            temp_spot_light, movement_type="strobe", end_frame=24, intensity=1.0
        )
        assert isinstance(result, dict)

    async def test_light_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_animate_light("NonExistentLight_XYZ_999", "flicker")


# ---------------------------------------------------------------------------
# daz_create_light_sequence
# ---------------------------------------------------------------------------

class TestCreateLightSequence:
    async def test_day_to_night(self, live_client, figure_label):
        before = await daz_list_lights()
        result = await daz_create_light_sequence(
            sequence_type="day-to-night", subject_label=figure_label
        )
        assert isinstance(result, dict)
        await _delete_lights_created_after(before.get("lights", []))

    async def test_without_subject(self, live_client):
        before = await daz_list_lights()
        result = await daz_create_light_sequence(sequence_type="night-to-dawn")
        assert isinstance(result, dict)
        await _delete_lights_created_after(before.get("lights", []))


# ---------------------------------------------------------------------------
# daz_set_scene_atmosphere
# ---------------------------------------------------------------------------

class TestSetSceneAtmosphere:
    async def test_set_environment_intensity(self, live_client):
        result = await daz_set_scene_atmosphere(environment_intensity=0.8)
        assert isinstance(result, dict)

    async def test_set_environment_mode(self, live_client):
        # Mode 1 = scene, Mode 2 = dome — try a non-destructive value
        result = await daz_set_scene_atmosphere(environment_mode=1)
        assert isinstance(result, dict)

    async def test_set_both(self, live_client):
        result = await daz_set_scene_atmosphere(
            environment_mode=1, environment_intensity=1.0
        )
        assert isinstance(result, dict)

    async def test_no_args_still_returns(self, live_client):
        result = await daz_set_scene_atmosphere()
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_apply_visual_style
# ---------------------------------------------------------------------------

class TestApplyVisualStyle:
    async def test_cinematic_style(self, live_client, figure_label):
        before = await daz_list_lights()
        result = await daz_apply_visual_style("cinematic", subject_label=figure_label)
        assert isinstance(result, dict)
        await _delete_lights_created_after(before.get("lights", []))

    async def test_style_without_subject(self, live_client):
        before = await daz_list_lights()
        result = await daz_apply_visual_style("cinematic")
        assert isinstance(result, dict)
        await _delete_lights_created_after(before.get("lights", []))
