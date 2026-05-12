"""Integration tests — camera management and cinematic composition.

Tools covered
-------------
- daz_set_active_camera
- daz_orbit_camera_around
- daz_frame_camera_to_node
- daz_save_camera_preset / daz_load_camera_preset
- daz_frame_shot
- daz_apply_camera_angle
- daz_apply_composition_rule
- daz_animate_camera_movement
- daz_create_camera_path
- daz_set_focus_point
- daz_animate_focus_pull
- daz_setup_shot_coverage
- daz_create_camera_rig
- daz_plan_shot
- daz_create_storyboard

Note: daz_create_camera / daz_list_cameras / daz_delete_node are covered in
test_phase5_integration.py and are used here only as test helpers.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_animate_camera_movement,
    daz_animate_focus_pull,
    daz_apply_camera_angle,
    daz_apply_composition_rule,
    daz_clear_animation,
    daz_create_camera_path,
    daz_create_camera_rig,
    daz_create_storyboard,
    daz_delete_node,
    daz_frame_camera_to_node,
    daz_frame_shot,
    daz_list_cameras,
    daz_load_camera_preset,
    daz_orbit_camera_around,
    daz_plan_shot,
    daz_save_camera_preset,
    daz_set_active_camera,
    daz_set_focus_point,
    daz_setup_shot_coverage,
)


# ---------------------------------------------------------------------------
# daz_set_active_camera
# ---------------------------------------------------------------------------

class TestSetActiveCamera:
    async def test_set_temp_camera_active(self, live_client, temp_camera):
        result = await daz_set_active_camera(temp_camera)
        assert isinstance(result, dict)

    async def test_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_set_active_camera("NonExistentCamera_XYZ_999")


# ---------------------------------------------------------------------------
# daz_orbit_camera_around
# ---------------------------------------------------------------------------

class TestOrbitCameraAround:
    async def test_orbit_around_figure(self, live_client, temp_camera, figure_label):
        result = await daz_orbit_camera_around(
            camera_label=temp_camera,
            target_label=figure_label,
            distance=200.0,
            angle_horizontal=45.0,
            angle_vertical=15.0,
        )
        assert isinstance(result, dict)

    async def test_various_angles(self, live_client, temp_camera, figure_label):
        for h_angle in [0.0, 90.0, 180.0]:
            result = await daz_orbit_camera_around(
                temp_camera, figure_label, distance=150.0,
                angle_horizontal=h_angle, angle_vertical=0.0,
            )
            assert isinstance(result, dict)

    async def test_camera_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_orbit_camera_around("NonExistentCamera_XYZ", figure_label)

    async def test_target_not_found_raises(self, live_client, temp_camera):
        with pytest.raises(ToolError):
            await daz_orbit_camera_around(temp_camera, "NonExistentTarget_XYZ")


# ---------------------------------------------------------------------------
# daz_frame_camera_to_node
# ---------------------------------------------------------------------------

class TestFrameCameraToNode:
    async def test_frame_to_figure(self, live_client, temp_camera, figure_label):
        result = await daz_frame_camera_to_node(temp_camera, figure_label)
        assert isinstance(result, dict)

    async def test_with_explicit_distance(self, live_client, temp_camera, figure_label):
        result = await daz_frame_camera_to_node(temp_camera, figure_label, distance=300.0)
        assert isinstance(result, dict)

    async def test_camera_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_frame_camera_to_node("NonExistentCamera_XYZ", figure_label)


# ---------------------------------------------------------------------------
# daz_save_camera_preset / daz_load_camera_preset
# ---------------------------------------------------------------------------

class TestCameraPreset:
    async def test_save_and_load_roundtrip(self, live_client, temp_camera):
        # Save — returns {"preset": {"label": ..., "transforms": {...}}}
        saved = await daz_save_camera_preset(temp_camera)
        assert isinstance(saved, dict)
        # Load expects the inner preset dict, not the wrapper
        preset_data = saved.get("preset", saved)
        result = await daz_load_camera_preset(temp_camera, preset_data)
        assert isinstance(result, dict)

    async def test_save_returns_position_data(self, live_client, temp_camera):
        result = await daz_save_camera_preset(temp_camera)
        assert isinstance(result, dict)
        text = str(result).lower()
        assert any(k in text for k in ["x", "y", "z", "position", "translation"])

    async def test_camera_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_save_camera_preset("NonExistentCamera_XYZ_999")


# ---------------------------------------------------------------------------
# daz_frame_shot
# ---------------------------------------------------------------------------

class TestFrameShot:
    @pytest.mark.parametrize("shot_type", [
        "close-up", "medium-shot", "full-shot", "wide-shot",
    ])
    async def test_shot_types(self, live_client, temp_camera, figure_label, shot_type):
        result = await daz_frame_shot(temp_camera, figure_label, shot_type=shot_type)
        assert isinstance(result, dict)

    async def test_camera_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_frame_shot("NonExistentCamera_XYZ", figure_label)

    async def test_subject_not_found_raises(self, live_client, temp_camera):
        with pytest.raises(ToolError):
            await daz_frame_shot(temp_camera, "NonExistentSubject_XYZ")


# ---------------------------------------------------------------------------
# daz_apply_camera_angle
# ---------------------------------------------------------------------------

class TestApplyCameraAngle:
    @pytest.mark.parametrize("angle", [
        "eye-level", "high-angle", "low-angle", "over-shoulder",
    ])
    async def test_standard_angles(self, live_client, temp_camera, figure_label, angle):
        result = await daz_apply_camera_angle(temp_camera, figure_label, angle=angle)
        assert isinstance(result, dict)

    async def test_dutch_angle(self, live_client, temp_camera, figure_label):
        result = await daz_apply_camera_angle(temp_camera, figure_label, angle="dutch-angle")
        assert isinstance(result, dict)

    async def test_camera_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_apply_camera_angle("NonExistentCamera_XYZ", figure_label)


# ---------------------------------------------------------------------------
# daz_apply_composition_rule
# ---------------------------------------------------------------------------

class TestApplyCompositionRule:
    @pytest.mark.parametrize("rule", [
        "rule-of-thirds", "center-frame",
    ])
    async def test_composition_rules(self, live_client, temp_camera, figure_label, rule):
        result = await daz_apply_composition_rule(temp_camera, figure_label, rule=rule)
        assert isinstance(result, dict)

    async def test_camera_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_apply_composition_rule("NonExistentCamera_XYZ", figure_label)


# ---------------------------------------------------------------------------
# daz_animate_camera_movement
# ---------------------------------------------------------------------------

class TestAnimateCameraMovement:
    @pytest_asyncio.fixture()
    async def clean_camera(self, live_client, temp_camera):
        yield temp_camera
        # Clear animation keyframes after test
        try:
            await daz_clear_animation(temp_camera, "XTranslate")
        except Exception:
            pass

    @pytest.mark.parametrize("movement", ["dolly-in", "pan-left", "tilt-up"])
    async def test_movement_types(self, live_client, clean_camera, movement):
        # Signature: (camera_label, movement_type, start_frame=0, end_frame=120, intensity=1.0)
        result = await daz_animate_camera_movement(
            clean_camera, movement_type=movement, start_frame=0, end_frame=30
        )
        assert isinstance(result, dict)

    async def test_handheld_shake(self, live_client, clean_camera):
        result = await daz_animate_camera_movement(
            clean_camera, movement_type="handheld-shake", start_frame=0, end_frame=24, intensity=0.5
        )
        assert isinstance(result, dict)

    async def test_camera_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_animate_camera_movement("NonExistentCamera_XYZ", "dolly-in")


# ---------------------------------------------------------------------------
# daz_create_camera_path
# ---------------------------------------------------------------------------

class TestCreateCameraPath:
    async def test_two_waypoint_path(self, live_client, temp_camera):
        # Signature: (camera_label, waypoints, easing="smooth", aim_at_target=None)
        result = await daz_create_camera_path(
            camera_label=temp_camera,
            waypoints=[
                {"position": {"x": 0.0, "y": 150.0, "z": 300.0}, "frame": 0},
                {"position": {"x": 100.0, "y": 150.0, "z": 200.0}, "frame": 60},
            ],
            easing="smooth",
        )
        assert isinstance(result, dict)
        # Clean up keyframes
        try:
            await daz_clear_animation(temp_camera, "XTranslate")
        except Exception:
            pass

    async def test_camera_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_create_camera_path(
                "NonExistentCamera_XYZ",
                waypoints=[{"x": 0, "y": 150, "z": 300}],
            )


# ---------------------------------------------------------------------------
# daz_set_focus_point
# ---------------------------------------------------------------------------

class TestSetFocusPoint:
    async def test_set_focus_to_figure(self, live_client, temp_camera, figure_label):
        result = await daz_set_focus_point(temp_camera, target_label=figure_label)
        assert isinstance(result, dict)

    async def test_set_focus_by_distance(self, live_client, temp_camera):
        # Signature: (camera_label, target_label=None, focal_distance=None)
        result = await daz_set_focus_point(temp_camera, focal_distance=200.0)
        assert isinstance(result, dict)

    async def test_camera_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_set_focus_point("NonExistentCamera_XYZ", target_label=figure_label)


# ---------------------------------------------------------------------------
# daz_animate_focus_pull
# ---------------------------------------------------------------------------

class TestAnimateFocusPull:
    async def test_focus_pull_by_distance(self, live_client, temp_camera):
        result = await daz_animate_focus_pull(
            temp_camera, from_distance=100.0, to_distance=300.0, start_frame=0, end_frame=30,
        )
        assert isinstance(result, dict)

    async def test_camera_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_animate_focus_pull("NonExistentCamera_XYZ")


# ---------------------------------------------------------------------------
# daz_setup_shot_coverage
# ---------------------------------------------------------------------------

class TestSetupShotCoverage:
    async def test_standard_coverage(self, live_client, figure_label):
        result = await daz_setup_shot_coverage(figure_label, coverage_type="standard")
        assert isinstance(result, dict)
        # Clean up cameras that were created
        cameras_created = result.get("cameras", [])
        for cam in cameras_created:
            label = cam if isinstance(cam, str) else cam.get("label", "")
            if label:
                try:
                    await daz_delete_node(label)
                except Exception:
                    pass

    async def test_dramatic_coverage(self, live_client, figure_label):
        result = await daz_setup_shot_coverage(figure_label, coverage_type="dramatic")
        assert isinstance(result, dict)
        cameras_created = result.get("cameras", [])
        for cam in cameras_created:
            label = cam if isinstance(cam, str) else cam.get("label", "")
            if label:
                try:
                    await daz_delete_node(label)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# daz_create_camera_rig
# ---------------------------------------------------------------------------

class TestCreateCameraRig:
    async def test_creates_rig(self, live_client):
        result = await daz_create_camera_rig(rig_name="TestRig_Temp")
        assert isinstance(result, dict)
        # Clean up created cameras
        cameras = result.get("cameras", [])
        for cam in cameras:
            label = cam if isinstance(cam, str) else cam.get("label", "")
            if label:
                try:
                    await daz_delete_node(label)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# daz_plan_shot
# ---------------------------------------------------------------------------

class TestPlanShot:
    async def test_medium_shot_plan(self, live_client, figure_label):
        result = await daz_plan_shot(shot_type="medium-shot", subject_label=figure_label)
        assert isinstance(result, dict)

    async def test_plan_without_subject(self, live_client):
        result = await daz_plan_shot(shot_type="wide-shot")
        assert isinstance(result, dict)

    async def test_close_up_plan(self, live_client, figure_label):
        result = await daz_plan_shot(shot_type="close-up", subject_label=figure_label)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_create_storyboard
# ---------------------------------------------------------------------------

class TestCreateStoryboard:
    async def test_two_shot_storyboard(self, live_client, figure_label):
        result = await daz_create_storyboard(
            title="Test Storyboard",
            shots=[
                {"shot_type": "wide-shot", "subject": figure_label, "notes": "Establish"},
                {"shot_type": "close-up", "subject": figure_label, "notes": "Reaction"},
            ],
        )
        assert isinstance(result, dict)
        # Clean up any cameras created
        cameras = result.get("cameras", [])
        for cam in cameras:
            label = cam if isinstance(cam, str) else cam.get("label", "")
            if label:
                try:
                    await daz_delete_node(label)
                except Exception:
                    pass

    async def test_empty_shots_raises(self, live_client):
        # The tool validates that shots must not be empty
        with pytest.raises(ToolError):
            await daz_create_storyboard(title="Empty Board", shots=[])
