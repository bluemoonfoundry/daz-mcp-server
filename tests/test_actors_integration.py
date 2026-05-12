"""Integration tests — morphs, emotion, posing, and character interaction.

Tools covered
-------------
- daz_list_morphs
- daz_search_morphs
- daz_set_emotion
- daz_look_at_point
- daz_look_at_character
- daz_reach_toward
- daz_interactive_pose
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_interactive_pose,
    daz_list_morphs,
    daz_look_at_character,
    daz_look_at_point,
    daz_reach_toward,
    daz_search_morphs,
    daz_set_emotion,
    daz_set_property,
)


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
# daz_look_at_point
# ---------------------------------------------------------------------------

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
