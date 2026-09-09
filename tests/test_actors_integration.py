"""Integration tests — morphs, emotion, posing, and character interaction.

Tools covered
-------------
- daz_list_morphs
- daz_search_morphs
- daz_set_emotion
- daz_set_body_language
- daz_direct_gaze
- daz_look_at_point
- daz_look_at_character
- daz_reach_toward
- daz_interactive_pose
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.tools.figure import (
    daz_interactive_pose,
    daz_look_at_character,
    daz_look_at_point,
    daz_reach_toward,
)
from vangard_daz_mcp.tools.morph import (
    daz_direct_gaze,
    daz_list_morphs,
    daz_search_morphs,
    daz_set_body_language,
    daz_set_emotion,
)
from vangard_daz_mcp.tools.scene import daz_restore_scene_state, daz_save_scene_state
from vangard_daz_mcp.tools.transform import daz_set_property


# ---------------------------------------------------------------------------
# Cleanup fixtures
#
# daz_save_scene_state/daz_restore_scene_state now capture every skeleton's
# complete pose (bone rotations, morphs, and node properties -- via dazpy's
# DazSceneState/DazPose, not just the root transform), so a save/restore
# checkpoint restores whatever pose the figure(s) actually had before the
# test ran -- not a hardcoded zero baseline. This covers daz_set_emotion's
# morph changes as well as the bone rotations from daz_look_at_point,
# daz_look_at_character, daz_reach_toward, and daz_interactive_pose, and
# extends to every figure in the scene (not just the one named by
# figure_label), so it's safe to run against a scene with a pose you care
# about, not just a disposable/scratch one.
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def clean_emotion(live_client, figure_label):
    checkpoint = "_test_actors_emotion_checkpoint"
    await daz_save_scene_state(checkpoint)
    yield
    await daz_restore_scene_state(checkpoint)


@pytest_asyncio.fixture()
async def clean_pose(live_client, figure_label):
    checkpoint = "_test_actors_pose_checkpoint"
    await daz_save_scene_state(checkpoint)
    yield
    await daz_restore_scene_state(checkpoint)


@pytest_asyncio.fixture()
async def clean_pose_both(live_client, figure_label):
    """Same as clean_pose -- kept as a distinct name for tests that pose two figures.

    The underlying checkpoint already covers every figure in the scene, so
    there's no need to enumerate figures separately as the old
    daz_reset_pose-based version did.
    """
    checkpoint = "_test_actors_pose_both_checkpoint"
    await daz_save_scene_state(checkpoint)
    yield
    await daz_restore_scene_state(checkpoint)


# ---------------------------------------------------------------------------
# daz_list_morphs
# ---------------------------------------------------------------------------

class TestListMorphs:
    async def test_returns_dict(self, live_client, figure_label):
        result = await daz_list_morphs(figure_label)
        assert isinstance(result, dict)

    async def test_morphs_is_list(self, live_client, figure_label):
        result = await daz_list_morphs(figure_label, include_zero=True)
        morphs = result.get("morphs", result.get("properties", []))
        assert isinstance(morphs, list)

    async def test_has_morphs(self, live_client, figure_label):
        """Genesis figures always have dozens of morphs."""
        result = await daz_list_morphs(figure_label, include_zero=True)
        morphs = result.get("morphs", result.get("properties", []))
        assert len(morphs) > 0

    async def test_morph_has_name(self, live_client, figure_label):
        result = await daz_list_morphs(figure_label, include_zero=True)
        morphs = result.get("morphs", result.get("properties", []))
        if morphs:
            first = morphs[0]
            assert any(k in first for k in ["name", "label"])

    async def test_include_zero_false_returns_subset(self, live_client, figure_label):
        all_morphs = await daz_list_morphs(figure_label, include_zero=True)
        active_morphs = await daz_list_morphs(figure_label, include_zero=False)
        all_count = len(all_morphs.get("morphs", all_morphs.get("properties", [])))
        active_count = len(active_morphs.get("morphs", active_morphs.get("properties", [])))
        assert active_count <= all_count

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_list_morphs("NonExistentNode_XYZ_999")


# ---------------------------------------------------------------------------
# daz_search_morphs
# ---------------------------------------------------------------------------

class TestSearchMorphs:
    async def test_returns_dict(self, live_client, figure_label):
        result = await daz_search_morphs(figure_label, "head", include_zero=True)
        assert isinstance(result, dict)

    async def test_search_finds_results(self, live_client, figure_label):
        """Genesis figures always have head-related morphs."""
        result = await daz_search_morphs(figure_label, "head", include_zero=True)
        morphs = result.get("morphs", result.get("results", result.get("properties", [])))
        assert isinstance(morphs, list)

    async def test_results_match_pattern(self, live_client, figure_label):
        result = await daz_search_morphs(figure_label, "smile", include_zero=True)
        morphs = result.get("morphs", result.get("results", result.get("properties", [])))
        if morphs:
            for morph in morphs:
                name = (morph.get("label") or morph.get("name") or "").lower()
                assert "smile" in name

    async def test_no_match_returns_empty(self, live_client, figure_label):
        result = await daz_search_morphs(
            figure_label, "zzz_no_morph_matches_this_xyz", include_zero=True
        )
        morphs = result.get("morphs", result.get("results", result.get("properties", [])))
        assert isinstance(morphs, list)
        assert len(morphs) == 0

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_search_morphs("NonExistentNode_XYZ_999", "smile")


# ---------------------------------------------------------------------------
# daz_set_emotion
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clean_emotion")
class TestSetEmotion:
    async def test_happy_emotion(self, live_client, figure_label):
        result = await daz_set_emotion(figure_label, "happy", intensity=0.5)
        assert isinstance(result, dict)

    async def test_neutral_emotion(self, live_client, figure_label):
        result = await daz_set_emotion(figure_label, "neutral", intensity=1.0)
        assert isinstance(result, dict)

    async def test_sad_emotion(self, live_client, figure_label):
        result = await daz_set_emotion(figure_label, "sad", intensity=0.3)
        assert isinstance(result, dict)

    async def test_intensity_zero_clears(self, live_client, figure_label):
        await daz_set_emotion(figure_label, "happy", intensity=0.8)
        result = await daz_set_emotion(figure_label, "happy", intensity=0.0)
        assert isinstance(result, dict)

    @pytest.mark.parametrize("emotion", [
        "happy", "sad", "angry", "surprised", "neutral", "confident"
    ])
    async def test_standard_emotions(self, live_client, figure_label, emotion):
        result = await daz_set_emotion(figure_label, emotion, intensity=0.5)
        assert isinstance(result, dict)

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_set_emotion("NonExistentNode_XYZ_999", "happy")


# ---------------------------------------------------------------------------
# daz_set_body_language
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clean_pose")
class TestSetBodyLanguage:
    @pytest.mark.parametrize("posture", ["confident", "defensive", "relaxed", "tense"])
    async def test_standard_postures(self, live_client, figure_label, posture):
        result = await daz_set_body_language(figure_label, posture, intensity=0.8)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result.get("applied"), (
            f"No bones were adjusted for posture {posture!r} — bone names may not "
            f"match this figure's generation. Result: {result}"
        )

    async def test_intensity_scales_value(self, live_client, figure_label):
        full = await daz_set_body_language(figure_label, "confident", intensity=1.0)
        half = await daz_set_body_language(figure_label, "confident", intensity=0.5)
        full_values = {a["bone"]: a["value"] for a in full["applied"]}
        half_values = {a["bone"]: a["value"] for a in half["applied"]}
        assert full_values, "No bones were adjusted — cannot verify intensity scaling"
        for bone, value in half_values.items():
            assert value == pytest.approx(full_values[bone] * 0.5)

    async def test_unknown_posture_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_set_body_language(figure_label, "nonexistent_posture_xyz")

    async def test_invalid_intensity_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_set_body_language(figure_label, "confident", intensity=1.5)

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_set_body_language("NonExistentNode_XYZ_999", "confident")


# ---------------------------------------------------------------------------
# daz_direct_gaze
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clean_pose")
class TestDirectGaze:
    @pytest.mark.parametrize("direction", ["up", "down", "left", "right", "away", "camera"])
    async def test_standard_directions(self, live_client, figure_label, direction):
        result = await daz_direct_gaze(figure_label, direction)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result.get("applied"), f"No bones rotated for direction {direction!r}. Result: {result}"

    async def test_character_direction(self, live_client, figure_label):
        # Self-target rather than a second figure or a scene-specific named
        # asset (e.g. a particular camera) -- always resolvable regardless
        # of what else is loaded, and daz_direct_gaze's "character" mode
        # accepts any node label, including the figure's own.
        result = await daz_direct_gaze(figure_label, "character", target_label=figure_label)
        assert result["success"] is True
        assert result.get("applied"), f"No bones rotated for character direction. Result: {result}"

    async def test_character_direction_requires_target(self, live_client, figure_label):
        with pytest.raises(ToolError, match="target_label"):
            await daz_direct_gaze(figure_label, "character")

    async def test_target_not_found_returns_unsuccessful(self, live_client, figure_label):
        # Unlike a missing figure_label (raises ToolError), a missing gaze
        # target is reported in the result rather than raised.
        result = await daz_direct_gaze(
            figure_label, "character", target_label="NonExistentTarget_XYZ_999"
        )
        assert result["success"] is False

    async def test_unknown_direction_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_direct_gaze(figure_label, "nonexistent_direction_xyz")

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_direct_gaze("NonExistentNode_XYZ_999", "left")


# ---------------------------------------------------------------------------
# daz_look_at_point
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clean_pose")
class TestLookAtPoint:
    # Targets are deliberately off-axis so rotation is large and visually obvious.
    # Character stands at origin facing +Z; looking hard right (+X) forces ~90° head turn.

    async def test_head_mode(self, live_client, figure_label):
        # Hard right: angleY ≈ 90°, clearly visible head turn
        result = await daz_look_at_point(figure_label, 300.0, 150.0, 0.0, mode="head")
        assert isinstance(result, dict)
        assert result.get("rotatedBones"), (
            f"No bones were rotated — DazScript bone names may not match this figure generation. "
            f"Full result: {result}"
        )

    async def test_eyes_mode(self, live_client, figure_label):
        # Hard left: forces eye rotation
        result = await daz_look_at_point(figure_label, -300.0, 155.0, 0.0, mode="eyes")
        assert isinstance(result, dict)
        assert result.get("rotatedBones"), f"No eye bones rotated. Result: {result}"

    async def test_full_mode(self, live_client, figure_label):
        # Far right and high up: forces multi-bone cascade
        result = await daz_look_at_point(figure_label, 250.0, 250.0, -100.0, mode="full")
        assert isinstance(result, dict)
        assert len(result.get("rotatedBones", [])) >= 2, (
            f"Expected ≥2 bones rotated in full mode, got: {result.get('rotatedBones')}"
        )

    async def test_torso_mode(self, live_client, figure_label):
        # Behind and to the left: torso must turn substantially
        result = await daz_look_at_point(figure_label, -200.0, 120.0, -150.0, mode="torso")
        assert isinstance(result, dict)
        assert result.get("rotatedBones"), f"No bones rotated in torso mode. Result: {result}"

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_look_at_point("NonExistentNode_XYZ_999", 0, 0, 0)


# ---------------------------------------------------------------------------
# daz_look_at_character
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clean_pose_both")
class TestLookAtCharacter:
    async def test_look_at_second_character(
        self, live_client, figure_label, second_figure_label
    ):
        result = await daz_look_at_character(figure_label, second_figure_label)
        assert isinstance(result, dict)
        assert result.get("rotatedBones"), (
            f"No bones were rotated — check bone name compatibility. Result: {result}"
        )

    async def test_head_mode(self, live_client, figure_label, second_figure_label):
        result = await daz_look_at_character(
            figure_label, second_figure_label, mode="head"
        )
        assert isinstance(result, dict)
        assert result.get("rotatedBones"), f"No head bones rotated. Result: {result}"

    async def test_source_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_look_at_character("NonExistentSource_XYZ", figure_label)

    async def test_target_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_look_at_character(figure_label, "NonExistentTarget_XYZ")


# ---------------------------------------------------------------------------
# daz_reach_toward
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clean_pose")
class TestReachToward:
    async def test_right_arm(self, live_client, figure_label):
        result = await daz_reach_toward(figure_label, "right", 50.0, 120.0, 80.0)
        assert isinstance(result, dict)
        bones = [b for b in result.get("bones", []) if b is not None]
        assert bones, f"No arm bones were positioned. Result: {result}"

    async def test_left_arm(self, live_client, figure_label):
        result = await daz_reach_toward(figure_label, "left", -50.0, 120.0, 80.0)
        assert isinstance(result, dict)
        bones = [b for b in result.get("bones", []) if b is not None]
        assert bones, f"No arm bones were positioned. Result: {result}"

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_reach_toward("NonExistentNode_XYZ_999", "right", 0, 0, 0)


# ---------------------------------------------------------------------------
# daz_interactive_pose
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clean_pose_both")
class TestInteractivePose:
    async def test_face_each_other(
        self, live_client, figure_label, second_figure_label
    ):
        result = await daz_interactive_pose(
            figure_label, second_figure_label, interaction_type="face-each-other"
        )
        assert isinstance(result, dict)

    async def test_handshake_pose(
        self, live_client, figure_label, second_figure_label
    ):
        result = await daz_interactive_pose(
            figure_label, second_figure_label, interaction_type="handshake"
        )
        assert isinstance(result, dict)

    async def test_node_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_interactive_pose(figure_label, "NonExistentTarget_XYZ")
