"""Integration tests — high-level cinematic and choreography tools.

Tools covered
-------------
- daz_create_shot_sequence
- daz_animate_conversation
- daz_create_scene
- daz_create_character_path
- daz_arrange_characters
- daz_choreograph_action
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_animate_conversation,
    daz_arrange_characters,
    daz_choreograph_action,
    daz_clear_animation,
    daz_create_character_path,
    daz_create_scene,
    daz_create_shot_sequence,
    daz_delete_node,
    daz_list_cameras,
)


# ---------------------------------------------------------------------------
# daz_create_shot_sequence
# ---------------------------------------------------------------------------

class TestCreateShotSequence:
    async def test_dialogue_sequence(self, live_client, figure_label):
        before_cameras = await daz_list_cameras()
        result = await daz_create_shot_sequence(
            sequence_type="establishing-medium-closeup",
            characters=[figure_label],
            duration=120,
        )
        assert isinstance(result, dict)
        # Clean up any cameras created
        after_cameras = await daz_list_cameras()
        before_labels = {c.get("label") for c in before_cameras.get("cameras", [])}
        for cam in after_cameras.get("cameras", []):
            if cam.get("label") not in before_labels:
                try:
                    await daz_delete_node(cam["label"])
                except Exception:
                    pass

    async def test_two_character_sequence(
        self, live_client, figure_label, second_figure_label
    ):
        before_cameras = await daz_list_cameras()
        result = await daz_create_shot_sequence(
            sequence_type="shot-reverse-shot",
            characters=[figure_label, second_figure_label],
        )
        assert isinstance(result, dict)
        after_cameras = await daz_list_cameras()
        before_labels = {c.get("label") for c in before_cameras.get("cameras", [])}
        for cam in after_cameras.get("cameras", []):
            if cam.get("label") not in before_labels:
                try:
                    await daz_delete_node(cam["label"])
                except Exception:
                    pass

    async def test_empty_characters_ok(self, live_client):
        result = await daz_create_shot_sequence(
            sequence_type="establishing-medium-closeup", characters=[]
        )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_animate_conversation
# ---------------------------------------------------------------------------

class TestAnimateConversation:
    async def test_two_character_conversation(
        self, live_client, figure_label, second_figure_label
    ):
        result = await daz_animate_conversation(
            char1_label=figure_label,
            char2_label=second_figure_label,
            dialogue_beats=[
                {"speaker": figure_label, "startFrame": 0, "endFrame": 30, "emotion": "neutral"},
                {"speaker": second_figure_label, "startFrame": 30, "endFrame": 60, "emotion": "neutral"},
            ],
        )
        assert isinstance(result, dict)

    async def test_minimal_conversation(self, live_client, figure_label, second_figure_label):
        """No beats provided — function uses defaults."""
        result = await daz_animate_conversation(
            figure_label, second_figure_label,
        )
        assert isinstance(result, dict)

    async def test_node_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_animate_conversation(figure_label, "NonExistentTarget_XYZ")


# ---------------------------------------------------------------------------
# daz_create_scene
# ---------------------------------------------------------------------------

class TestCreateScene:
    async def test_description_only(self, live_client):
        """Simple scene description — no specific characters required."""
        result = await daz_create_scene(
            description="A minimal test scene with soft lighting"
        )
        assert isinstance(result, dict)

    async def test_with_characters(self, live_client, figure_label):
        result = await daz_create_scene(
            description="A dramatic portrait scene",
            characters=[figure_label],
        )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_create_character_path
# ---------------------------------------------------------------------------

class TestCreateCharacterPath:
    @pytest_asyncio.fixture()
    async def clean_animation(self, live_client, figure_label):
        yield
        try:
            await daz_clear_animation(figure_label, "XTranslate")
            await daz_clear_animation(figure_label, "ZTranslate")
        except Exception:
            pass

    async def test_two_waypoint_path(
        self, live_client, figure_label, clean_animation
    ):
        result = await daz_create_character_path(
            character_label=figure_label,
            waypoints=[
                {"position": {"x": 0.0, "y": 0.0, "z": 0.0}, "frame": 0},
                {"position": {"x": 100.0, "y": 0.0, "z": 0.0}, "frame": 60},
            ],
        )
        assert isinstance(result, dict)

    async def test_three_waypoint_arc(
        self, live_client, figure_label, clean_animation
    ):
        result = await daz_create_character_path(
            character_label=figure_label,
            waypoints=[
                {"position": {"x": -100.0, "y": 0.0, "z": 0.0}, "frame": 0},
                {"position": {"x": 0.0, "y": 0.0, "z": 50.0}, "frame": 45},
                {"position": {"x": 100.0, "y": 0.0, "z": 0.0}, "frame": 90},
            ],
            walking_style="casual",
        )
        assert isinstance(result, dict)

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_create_character_path(
                "NonExistentNode_XYZ_999",
                waypoints=[{"x": 0, "y": 0, "z": 0}],
            )


# ---------------------------------------------------------------------------
# daz_arrange_characters
# ---------------------------------------------------------------------------

class TestArrangeCharacters:
    @pytest.mark.parametrize("arrangement", ["conversation-circle", "line", "semicircle"])
    async def test_single_character_arrangements(
        self, live_client, figure_label, arrangement
    ):
        result = await daz_arrange_characters(
            characters=[figure_label],
            arrangement=arrangement,
        )
        assert isinstance(result, dict)

    async def test_two_character_line(
        self, live_client, figure_label, second_figure_label
    ):
        result = await daz_arrange_characters(
            characters=[figure_label, second_figure_label],
            arrangement="line",
        )
        assert isinstance(result, dict)

    async def test_with_center_position(self, live_client, figure_label):
        result = await daz_arrange_characters(
            characters=[figure_label],
            arrangement="conversation-circle",
            center_position={"x": 0.0, "y": 0.0, "z": 0.0},
        )
        assert isinstance(result, dict)

    async def test_empty_list_ok(self, live_client):
        result = await daz_arrange_characters(characters=[], arrangement="circle")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_choreograph_action
# ---------------------------------------------------------------------------

class TestchoreographAction:
    async def test_single_character_action(self, live_client, figure_label):
        """Single character returns early with suggestions (needs 2 for full choreography)."""
        result = await daz_choreograph_action(
            action_type="dance",
            characters=[figure_label],
        )
        assert isinstance(result, dict)

    async def test_two_character_handshake(
        self, live_client, figure_label, second_figure_label
    ):
        result = await daz_choreograph_action(
            action_type="handshake",
            characters=[figure_label, second_figure_label],
        )
        assert isinstance(result, dict)

    async def test_two_character_fight(
        self, live_client, figure_label, second_figure_label
    ):
        result = await daz_choreograph_action(
            action_type="fight",
            characters=[figure_label, second_figure_label],
        )
        assert isinstance(result, dict)

    async def test_empty_characters_ok(self, live_client):
        result = await daz_choreograph_action(action_type="dance", characters=[])
        assert isinstance(result, dict)
