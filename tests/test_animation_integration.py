"""Integration tests — keyframes, timeline, and character timing.

Tools covered
-------------
- daz_get_animation_info
- daz_set_frame_range
- daz_set_frame
- daz_set_keyframe
- daz_get_keyframes
- daz_remove_keyframe
- daz_clear_animation
- daz_time_expression
- daz_sync_character_beats
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_clear_animation,
    daz_get_animation_info,
    daz_get_keyframes,
    daz_remove_keyframe,
    daz_set_frame,
    daz_set_frame_range,
    daz_set_keyframe,
    daz_sync_character_beats,
    daz_time_expression,
)


# ---------------------------------------------------------------------------
# daz_get_animation_info
# ---------------------------------------------------------------------------

class TestGetAnimationInfo:
    async def test_returns_dict(self, live_client):
        result = await daz_get_animation_info()
        assert isinstance(result, dict)

    async def test_has_frame_range(self, live_client):
        result = await daz_get_animation_info()
        text = str(result).lower()
        assert any(k in text for k in ["start", "end", "frame", "range", "fps"])

    async def test_fps_is_positive(self, live_client):
        result = await daz_get_animation_info()
        fps = result.get("fps", result.get("frame_rate", None))
        if fps is not None:
            assert float(fps) > 0


# ---------------------------------------------------------------------------
# daz_set_frame_range
# ---------------------------------------------------------------------------

class TestSetFrameRange:
    @pytest_asyncio.fixture()
    async def restore_range(self, live_client):
        """Restore the original frame range after test."""
        info = await daz_get_animation_info()
        start = info.get("start_frame", info.get("start", 0))
        end = info.get("end_frame", info.get("end", 120))
        yield int(start), int(end)
        await daz_set_frame_range(int(start), int(end))

    async def test_sets_range(self, live_client, restore_range):
        result = await daz_set_frame_range(0, 60)
        assert isinstance(result, dict)

    async def test_range_reflected_in_info(self, live_client, restore_range):
        await daz_set_frame_range(0, 48)
        info = await daz_get_animation_info()
        end = info.get("end_frame", info.get("end", None))
        if end is not None:
            assert int(end) == 48


# ---------------------------------------------------------------------------
# daz_set_frame
# ---------------------------------------------------------------------------

class TestSetFrame:
    async def test_returns_dict(self, live_client):
        result = await daz_set_frame(0)
        assert isinstance(result, dict)

    async def test_set_middle_frame(self, live_client):
        info = await daz_get_animation_info()
        end = int(info.get("end_frame", info.get("end", 60)))
        mid = end // 2
        result = await daz_set_frame(mid)
        assert isinstance(result, dict)
        # Return to frame 0
        await daz_set_frame(0)


# ---------------------------------------------------------------------------
# daz_set_keyframe / daz_get_keyframes / daz_remove_keyframe / daz_clear_animation
# ---------------------------------------------------------------------------

class TestKeyframes:
    PROP = "XTranslate"

    @pytest_asyncio.fixture()
    async def clean_keyframes(self, live_client, figure_label):
        """Clear XTranslate animation before and after test."""
        await daz_clear_animation(figure_label, self.PROP)
        yield
        await daz_clear_animation(figure_label, self.PROP)

    async def test_set_keyframe(self, live_client, figure_label, clean_keyframes):
        result = await daz_set_keyframe(figure_label, self.PROP, frame=0, value=0.0)
        assert isinstance(result, dict)

    async def test_get_keyframes_after_set(self, live_client, figure_label, clean_keyframes):
        await daz_set_keyframe(figure_label, self.PROP, frame=0, value=0.0)
        await daz_set_keyframe(figure_label, self.PROP, frame=30, value=20.0)
        result = await daz_get_keyframes(figure_label, self.PROP)
        assert isinstance(result, dict)
        keys = result.get("keyframes", result.get("keys", []))
        assert len(keys) >= 2

    async def test_remove_keyframe(self, live_client, figure_label, clean_keyframes):
        await daz_set_keyframe(figure_label, self.PROP, frame=10, value=5.0)
        remove_result = await daz_remove_keyframe(figure_label, self.PROP, frame=10)
        assert isinstance(remove_result, dict)

    async def test_clear_animation(self, live_client, figure_label, clean_keyframes):
        await daz_set_keyframe(figure_label, self.PROP, frame=0, value=0.0)
        await daz_set_keyframe(figure_label, self.PROP, frame=20, value=10.0)
        clear_result = await daz_clear_animation(figure_label, self.PROP)
        assert isinstance(clear_result, dict)
        # After clear, keyframes should be empty
        result = await daz_get_keyframes(figure_label, self.PROP)
        keys = result.get("keyframes", result.get("keys", []))
        assert len(keys) == 0

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_set_keyframe("NonExistentNode_XYZ_999", self.PROP, 0, 0.0)


# ---------------------------------------------------------------------------
# daz_time_expression
# ---------------------------------------------------------------------------

class TestTimeExpression:
    @pytest_asyncio.fixture()
    async def clean_expression(self, live_client, figure_label):
        yield
        # Reset emotion morphs after test
        try:
            await daz_clear_animation(figure_label, "Mouth Open")
        except Exception:
            pass

    async def test_happy_expression(self, live_client, figure_label, clean_expression):
        result = await daz_time_expression(
            character_label=figure_label,
            emotion="happy",
            peak_frame=15,
            intensity=0.6,
            ease_in_frames=5,
            ease_out_frames=5,
        )
        assert isinstance(result, dict)

    async def test_zero_intensity(self, live_client, figure_label, clean_expression):
        result = await daz_time_expression(
            character_label=figure_label,
            emotion="neutral",
            peak_frame=10,
            intensity=0.0,
        )
        assert isinstance(result, dict)

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_time_expression("NonExistentNode_XYZ_999", "happy", peak_frame=10)


# ---------------------------------------------------------------------------
# daz_sync_character_beats
# ---------------------------------------------------------------------------

class TestSyncCharacterBeats:
    async def test_single_character_beat(self, live_client, figure_label):
        result = await daz_sync_character_beats(
            beat_frame=20,
            characters=[{"label": figure_label, "emotion": "surprised", "intensity": 0.5}],
        )
        assert isinstance(result, dict)

    async def test_two_character_beats(
        self, live_client, figure_label, second_figure_label
    ):
        result = await daz_sync_character_beats(
            beat_frame=30,
            characters=[
                {"label": figure_label, "emotion": "angry", "intensity": 0.7},
                {"label": second_figure_label, "emotion": "fearful", "intensity": 0.7},
            ],
            hold_frames=10,
        )
        assert isinstance(result, dict)

    async def test_empty_characters_ok(self, live_client):
        result = await daz_sync_character_beats(beat_frame=0, characters=[])
        assert isinstance(result, dict)
