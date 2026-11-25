"""Cinematography tools: shot composition, coverage, and camera/light rigs."""
from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path
from typing import Any

from fastmcp.exceptions import ToolError

from dazpy import shot_library as sl
from dazpy.exceptions import NodeNotFoundError
from dazpy.math3 import Vec3
from dazpy.shots import (CameraKeyframe, Keyframed, Lens, Placement, Sequence, Shot, Storyboard,
                         apply_shot)

from .._mcp import mcp, _execute_by_id
from .._client import get_scene
from .._errors import run_tool
from .. import _cinematic_lighting as _lighting
from .. import _shots
from .._emotions import AXIS_BY_PROPERTY, _EMOTION_DEFINITIONS, resolve_bone

_VALID_SHOT_TYPES = frozenset({
    "extreme-close-up", "close-up", "medium-close-up", "medium-shot",
    "medium-full", "full-shot", "wide-shot", "extreme-wide",
    "two-shot", "over-shoulder",
})

_VALID_MOODS = frozenset({
    "neutral", "dramatic", "happy", "sad", "tense", "romantic", "horror", "action",
})

_VALID_COMPOSITION_RULES = frozenset({
    "rule-of-thirds", "center-frame", "golden-ratio", "leading-lines",
})

#: plan_shot composition rule -> (subject screen x, camera elevation deg or None, note).
_PLAN_COMPOSITION: dict[str, tuple[float, float | None, str]] = {
    "rule-of-thirds": (sl.THIRD_X, None, "Subject on the right vertical third"),
    "center-frame": (0.0, None, "Subject centred: symmetric composition"),
    "golden-ratio": (sl.GOLDEN_X, None,
                     "Subject on the right golden section (0.382 / 0.618 split)"),
    "leading-lines": (-sl.THIRD_X, -10.0,
                      "Low angle, subject on the left third: the frame leads in"),
}

_PLAN_DESCRIPTIONS: dict[str, str] = {
    **{t: _shots.FRAMING_NOTES[s].capitalize() for t, s in _shots.SHOT_TYPES.items()},
    "two-shot": "Two characters framed together",
    "over-shoulder": "OTS: foreground shoulder, background face",
}

#: plan_shot mood -> lighting recommendation.
_PLAN_MOODS: dict[str, dict[str, Any]] = {
    "neutral": {"preset": "three-point", "keyAngle": 45, "keyFlux": 4000, "fillRatio": 0.5,
                "rimRatio": 0.3, "notes": "Balanced, versatile lighting"},
    "dramatic": {"preset": "rembrandt", "keyAngle": 45, "keyFlux": 6000, "fillRatio": 0.15,
                 "rimRatio": 0.5, "notes": "High contrast, shadowed fill side"},
    "happy": {"preset": "butterfly", "keyAngle": 0, "keyFlux": 5000, "fillRatio": 0.6,
              "rimRatio": 0.4, "notes": "Bright front light, even fill"},
    "sad": {"preset": "split", "keyAngle": 90, "keyFlux": 2500, "fillRatio": 0.1,
            "rimRatio": 0.2, "notes": "Low key, deep shadows"},
    "tense": {"preset": "loop", "keyAngle": 35, "keyFlux": 5500, "fillRatio": 0.2,
              "rimRatio": 0.6, "notes": "Hard key, strong rim separation"},
    "romantic": {"preset": "butterfly", "keyAngle": 10, "keyFlux": 1800, "fillRatio": 0.7,
                 "rimRatio": 0.3, "notes": "Soft, warm, flattering"},
    "horror": {"preset": "split", "keyAngle": 180, "keyFlux": 1500, "fillRatio": 0.05,
               "rimRatio": 0.1, "notes": "Under-lit or side-lit, minimal fill"},
    "action": {"preset": "three-point", "keyAngle": 30, "keyFlux": 7000, "fillRatio": 0.3,
               "rimRatio": 0.8, "notes": "High energy, strong rim for separation"},
}

#: Snake-case / short keys accepted in daz_create_storyboard shot dicts.
_STORYBOARD_ALIASES = {
    "shot_type": "shotType", "subject": "subjectLabel", "subject_label": "subjectLabel",
    "partner": "partnerLabel", "partner_label": "partnerLabel", "camera": "cameraLabel",
    "camera_label": "cameraLabel", "duration": "durationFrames",
    "duration_frames": "durationFrames",
    "focal_length": "focalLength",
}

_VALID_ENV_MODES = {0, 1, 2, 3}

_VALID_VISUAL_STYLES = frozenset({
    "cinematic", "noir", "golden-hour", "blue-hour",
    "high-key", "low-key", "documentary", "fantasy",
})


# ---------------------------------------------------------------------------
# Phase 4.4: Shot Sequence & Conversation tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_create_shot_sequence(
    sequence_type: str,
    characters: list[str],
    duration: int = 120,
    side: int = 1,
) -> dict[str, Any]:
    """Create a multi-camera shot sequence for cinematic storytelling.

    Builds the shots with ``dazpy.shot_library`` and creates one camera per
    shot, labelled with its shot id (e.g. ``WS_Alice``, ``OTS_Bob_over_Alice``).

    Args:
        sequence_type: Type of sequence to create. Options:
            - "establishing-medium-closeup": Wide (35mm) -> medium (50mm) ->
              close-up (85mm) of the first character, frames split in thirds.
            - "shot-reverse-shot": Over-the-shoulder pair for a conversation.
              Requires 2 characters. Both cameras stay on one side of the line
              between them (the 180-degree rule), so eyelines match across the
              cut; frames split 50/50.
            - "orbit": One camera circling the subject 360 degrees, keyed every 15.
            - "push-in": One camera dollying from a wide shot to a close-up.
        characters: Character labels (1-2 depending on sequence). The first is
            the primary subject. With none, cameras frame the scene origin.
        duration: Total duration in frames (default: 120 = 4 seconds at 30fps).
        side: Which side of the line of action the shot-reverse-shot cameras
            stand on: 1 (default) = the first character's right as they face
            the second, -1 = the other side.

    Returns:
        Dict with:
        - cameras: list of {label, shotId, position, focalLength, frameRange, animated}
        - totalFrames, sequenceType, subject
        - continuity: 180-degree-rule issues (empty when every camera is on one side)

    Example:
        daz_create_shot_sequence("shot-reverse-shot", ["Alice", "Bob"], duration=240)
        # OTS_Bob_over_Alice (0-119), OTS_Alice_over_Bob (120-239)

    Notes:
        - Multi-shot sequences use frame ranges: render each camera for its range
        - Use daz_set_active_camera() to preview each camera angle
    """
    valid_types = ["establishing-medium-closeup", "shot-reverse-shot", "orbit", "push-in"]
    if sequence_type not in valid_types:
        raise ToolError(
            f"Invalid sequence_type '{sequence_type}'. Valid options: {', '.join(valid_types)}"
        )
    if sequence_type == "shot-reverse-shot" and len(characters) < 2:
        raise ToolError("shot-reverse-shot requires 2 characters")
    if duration < 10 or duration > 10000:
        raise ToolError("Duration must be between 10 and 10000 frames")
    if side not in (1, -1):
        raise ToolError("side must be 1 or -1")

    def _run() -> dict[str, Any]:
        scene = get_scene()
        if characters:
            names = characters[:2] if sequence_type == "shot-reverse-shot" else characters[:1]
            positions = {n: _shots.subject(scene, n).root for n in names}
            key = characters[0]
        else:
            key, positions = "origin", {"origin": Vec3(0.0, 0.0, 0.0)}
        end = duration - 1
        continuity: list[dict[str, Any]] = []
        if sequence_type == "establishing-medium-closeup":
            third = duration // 3
            ranges = [(0, third - 1), (third, 2 * third - 1), (2 * third, end)]
            shots = [replace(s, frame_range=r) for s, r in
                     zip(sl.subject_coverage(key, preset="standard").all_shots(), ranges)]
        elif sequence_type == "shot-reverse-shot":
            line = sl.LineOfAction.between(positions, characters[0], characters[1], side)
            half = duration // 2
            shots = list(sl.shot_reverse_shot(line, frame_ranges=((0, half - 1), (half, end))))
            continuity = _shots.issues(sl.check_axis(shots, line, positions))
        elif sequence_type == "orbit":
            shots = [sl.arc(key, start=0, end=end, radius=250.0, step_deg=15.0, positions=positions)]
        else:
            shots = [sl.push_in(positions, key, start=0, end=end, from_size="wide", to_size="close_up")]
        cams = sl.apply_coverage(scene, shots, subjects=positions)
        return {
            "cameras": [_shots.shot_summary(s, label, positions) for s, label in zip(shots, cams)],
            "totalFrames": duration,
            "sequenceType": sequence_type,
            "subject": characters[0] if characters else None,
            "continuity": continuity,
        }

    return await _shots.run(_run)


@mcp.tool()
async def daz_animate_conversation(
    char1_label: str,
    char2_label: str,
    dialogue_beats: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Choreograph an animated conversation between two characters.

    Automatically sets up keyframe animations for a dialogue sequence, including:
    - Look-at behavior (listener looks at speaker)
    - Emotion morphs timed to dialogue beats
    - Head/neck rotation for natural conversation dynamics

    Perfect for creating animated conversations without manually keyframing each movement.

    Args:
        char1_label: Label of first character
        char2_label: Label of second character
        dialogue_beats: List of dialogue beat dicts, each containing:
            - speaker: Label of who's speaking (must match char1_label or char2_label)
            - startFrame: Frame where beat starts (int)
            - endFrame: Frame where beat ends (int)
            - emotion: Emotion for speaker ("happy", "sad", "angry", "surprised", "neutral")
            - intensity: Optional emotion intensity 0.0-1.0 (default: 0.7)

    Returns:
        Dict with:
        - char1, char2: Character labels
        - beatsApplied: List of applied beats with actions performed
        - totalFrames: Total animation length
        - beatCount: Number of dialogue beats processed

    Example:
        # Create a 3-beat conversation
        result = daz_animate_conversation(
            "Alice",
            "Bob",
            [
                {
                    "speaker": "Alice",
                    "startFrame": 0,
                    "endFrame": 60,
                    "emotion": "happy",
                    "intensity": 0.8
                },
                {
                    "speaker": "Bob",
                    "startFrame": 60,
                    "endFrame": 120,
                    "emotion": "surprised",
                    "intensity": 0.9
                },
                {
                    "speaker": "Alice",
                    "startFrame": 120,
                    "endFrame": 180,
                    "emotion": "neutral"
                }
            ]
        )
        # Result shows 3 beats applied with emotion morphs and look-at animations

    Notes:
        - Characters automatically look at whoever is speaking
        - Emotion morphs are applied at beat start and held until beat end
        - Head and neck bones rotate for natural look-at behavior
        - Missing morphs are silently skipped (different Genesis generations have different morphs)
        - Use daz_set_frame() to preview animation at specific frames
        - Combine with daz_create_shot_sequence("shot-reverse-shot", ...) for camera angles
    """
    # Validate characters
    if not char1_label or not char2_label:
        raise ToolError("Both char1_label and char2_label are required")

    if char1_label == char2_label:
        raise ToolError("char1_label and char2_label must be different characters")

    beats = dialogue_beats or []

    # Validate each beat
    for i, beat in enumerate(beats):
        if "speaker" not in beat:
            raise ToolError(f"Beat {i+1}: 'speaker' field required")
        if "startFrame" not in beat:
            raise ToolError(f"Beat {i+1}: 'startFrame' field required")
        if "endFrame" not in beat:
            raise ToolError(f"Beat {i+1}: 'endFrame' field required")

        speaker = beat["speaker"]
        if speaker not in [char1_label, char2_label]:
            raise ToolError(
                f"Beat {i+1}: speaker '{speaker}' must be either '{char1_label}' or '{char2_label}'"
            )

        start = beat["startFrame"]
        end = beat["endFrame"]
        if not isinstance(start, int) or not isinstance(end, int):
            raise ToolError(f"Beat {i+1}: startFrame and endFrame must be integers")
        if start < 0 or end < 0:
            raise ToolError(f"Beat {i+1}: startFrame and endFrame must be non-negative")
        if end <= start:
            raise ToolError(f"Beat {i+1}: endFrame ({end}) must be > startFrame ({start})")

        # Validate emotion if present
        if "emotion" in beat:
            valid_emotions = ["happy", "sad", "angry", "surprised", "neutral"]
            if beat["emotion"] not in valid_emotions:
                raise ToolError(
                    f"Beat {i+1}: emotion '{beat['emotion']}' invalid. "
                    f"Valid: {', '.join(valid_emotions)}"
                )

    return await _execute_by_id("vangard-animate-conversation", {
        "char1Label": char1_label,
        "char2Label": char2_label,
        "dialogueBeats": beats,
    })


@mcp.tool()
async def daz_create_scene(
    description: str,
    characters: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a complete scene from a natural language description.

    Automatically creates a scene setup including lighting, cameras, and character
    positioning based on a text description. Uses template-based scene generation
    with keyword matching to identify scene types and apply appropriate setups.

    Perfect for quickly setting up common scene types without manual configuration.

    Supported Scene Types (detected via keywords):
        - "dining" / "dinner" / "meal" / "eat" - Dining/meal scene
        - "interview" / "meeting" / "business" - Interview/business meeting
        - "portrait" / "headshot" / "photo" - Portrait/photography
        - "conversation" / "talking" / "chat" - Conversation scene
        - Generic fallback for unrecognized descriptions

    Args:
        description: Natural language description of the scene.
            Examples:
            - "romantic dinner for two"
            - "job interview scene"
            - "professional portrait"
            - "two friends having a conversation"
            - "business meeting"

        characters: Optional list of character labels already loaded in the scene.
            Characters will be positioned appropriately for the scene type.
            If empty/None, scene will still be set up but positioning skipped.

    Returns:
        Dict with:
        - sceneType: Detected scene type ("dining", "interview", "portrait", "conversation",
          "generic")
        - description: Original description
        - charactersUsed: Number of characters processed
        - actions: List of actions performed (what was set up)
        - cameras: List of {type, purpose, label, shotId, position, focalLength, ...}
        - continuity: 180-degree-rule issues between the first two characters
        - suggestions: List of suggestions for improving the scene

    Example:
        # Romantic dinner scene
        result = daz_create_scene(
            "romantic dinner for two",
            ["Alice", "Bob"]
        )
        # Creates:
        # - Positions Alice and Bob facing each other
        # - Warm romantic lighting (2 spot lights)
        # - Wide shot camera
        # - Over-shoulder camera (for conversation)
        # - Suggestions: add table, plates, candles

        # Portrait setup
        result = daz_create_scene(
            "professional portrait",
            ["Genesis 9"]
        )
        # Creates:
        # - Three-point portrait lighting
        # - Close-up camera (50cm)
        # - Medium close-up camera (90cm)
        # - Suggestions: adjust expression, add backdrop

        # Job interview
        result = daz_create_scene(
            "job interview",
            ["Interviewer", "Candidate"]
        )
        # Creates:
        # - Characters positioned facing each other
        # - Professional three-point lighting
        # - Wide and medium shot cameras
        # - Suggestions: add desk, chairs, office props

    What Gets Created:
        1. **Lighting**: Scene-appropriate lighting setup (spot lights)
           - Dining: Warm romantic or standard dining lights
           - Interview: Professional three-point lighting
           - Portrait: Classic three-point portrait lighting
           - Conversation: Natural conversational lighting
           - Environment mode set to "Scene Only" (disables dome)

        2. **Character Positioning**: Logical positioning for scene type
           - Dining: Facing across table distance
           - Interview: Facing each other at interview distance
           - Conversation: Facing at conversation distance (closer than interview)

        3. **Cameras**: built with ``dazpy.shot_library`` and labelled with their
           shot ids (``MST_Alice-Bob``, ``OTS_Bob_over_Alice``, ``CU_Alice``...)
           - Dining: master + over-the-shoulder (2 characters)
           - Interview: master + medium single (2 characters)
           - Conversation: shot/reverse-shot pair on one side of the line
           - Portrait: close-up + medium close-up
           - Otherwise: wide + medium (master + medium with 2 characters)
           No characters: no cameras.

        4. **Suggestions**: Actionable next steps for scene enhancement

    Notes:
        - Requires characters to be already loaded in scene
        - Creates new cameras and lights (doesn't delete existing)
        - Scene type detection is keyword-based (simple matching)
        - Generic fallback if no template matches
        - Props are not automatically loaded (suggested in suggestions list)
        - All positioning uses world-space coordinates
        - Lighting intensities calibrated for Iray rendering

    Limitations:
        - Does not load props automatically (manual loading required)
        - Does not apply poses or emotions (use daz_set_emotion separately)
        - Simple keyword matching (not full NL understanding)
        - Limited to pre-defined scene templates
        - Works best with 1-2 characters

    Follow-up Actions:
        After scene generation, you can:
        - Load props manually with daz_load_file()
        - Apply character emotions with daz_set_emotion()
        - Fine-tune lighting with daz_set_property()
        - Adjust camera positions with daz_set_property()
        - Preview cameras with daz_set_active_camera()
    """
    # Validate description
    if not description or len(description.strip()) == 0:
        raise ToolError("Description cannot be empty")

    if len(description) > 500:
        raise ToolError("Description too long (max 500 characters)")

    # Validate characters
    chars = characters or []
    if len(chars) > 10:
        raise ToolError("Too many characters (max 10)")

    result = await _execute_by_id("vangard-create-scene", {
        "description": description,
        "characters": chars,
    })
    result = dict(result or {})
    scene_type = result.get("sceneType", "generic")

    def _cameras() -> dict[str, Any]:
        scene = get_scene()
        positions: dict[str, Vec3] = {}
        missing = []
        for label in chars[:2]:
            try:
                positions[label] = _shots.subject(scene, label).root
            except NodeNotFoundError:
                missing.append(label)
        plan = _scene_camera_plan(scene_type, list(positions), positions)
        shots = [s for s, _, _ in plan]
        cams = sl.apply_coverage(scene, shots, subjects=positions) if shots else {}
        continuity: list[dict[str, Any]] = []
        if len(positions) >= 2:
            keys = list(positions)
            line = sl.LineOfAction.between(positions, keys[0], keys[1])
            continuity = _shots.issues(sl.check_axis(shots, line, positions))
        return {
            "cameras": [{"type": kind, "purpose": purpose,
                         **_shots.shot_summary(s, label, positions)}
                        for (s, kind, purpose), label in zip(plan, cams)],
            "continuity": continuity,
            "missing": missing,
        }

    built = await _shots.run(_cameras)
    result["cameras"] = built["cameras"]
    result["continuity"] = built["continuity"]
    if built["missing"]:
        result.setdefault("suggestions", []).append(
            "Characters not found (no cameras for them): " + ", ".join(built["missing"]))
    return result


def _scene_camera_plan(scene_type: str, keys: list[str],
                       positions: dict[str, Vec3]) -> list[tuple[Shot, str, str]]:
    """``(shot, type, purpose)`` cameras for a ``daz_create_scene`` template."""
    if not keys:
        return []
    a = keys[0]
    line = sl.LineOfAction.between(positions, a, keys[1]) if len(keys) >= 2 else None
    wide = (_shots.size_shot("wide-shot", a, positions), "wide", "Establishing shot")
    medium = (_shots.size_shot("medium-shot", a, positions), "medium", "Medium framing")
    if scene_type == "portrait":
        return [(_shots.size_shot("close-up", a, positions), "close-up", "Face portrait"),
                (_shots.size_shot("medium-close-up", a, positions, azimuth=sl.SINGLE_OFFSET_DEG),
                 "medium-close-up", "Head and shoulders")]
    if line is None:
        return [wide, medium]
    if scene_type == "dining":
        return [(sl.master(line), "wide", "Establishing shot of the table"),
                (sl.over_the_shoulder(line, a, line.b), "over-shoulder", "Conversation angle")]
    if scene_type == "interview":
        return [(sl.master(line), "wide", "Establishing interview setup"),
                (sl.single(line, a, size="medium"), "medium", "Professional medium shot")]
    if scene_type == "conversation":
        ots = sl.shot_reverse_shot(line)
        return [(ots[0], "over-shoulder", f"Over {a}'s shoulder onto {line.b}"),
                (ots[1], "over-shoulder", f"Over {line.b}'s shoulder onto {a}")]
    return [(sl.master(line), "wide", "Establishing shot"), medium]


# ---------------------------------------------------------------------------
# Camera Movement & Animation Tools (Phase 4.5)
# ---------------------------------------------------------------------------


#: MCP movement type -> (dazpy.shot_library.camera_move kind, amount at intensity 1).
_CAMERA_MOVES: dict[str, tuple[str, float]] = {
    "dolly-in": ("dolly_in", 200.0), "dolly-out": ("dolly_out", 200.0),
    "pan-left": ("pan_left", 45.0), "pan-right": ("pan_right", 45.0),
    "tilt-up": ("tilt_up", 30.0), "tilt-down": ("tilt_down", 30.0),
    "crane-up": ("crane_up", 100.0), "crane-down": ("crane_down", 100.0),
    "handheld-shake": ("handheld", 5.0),
}


@mcp.tool()
async def daz_animate_camera_movement(
    camera_label: str,
    movement_type: str,
    start_frame: int = 0,
    end_frame: int = 120,
    intensity: float = 1.0,
) -> dict[str, Any]:
    """Animate common camera movements with keyframes.

    Starts from the camera's current position and rotation and keys the move
    at *start_frame* and *end_frame* (``dazpy.shot_library.camera_move``).
    Existing keys outside the move are kept, so moves on one camera chain.

    Args:
        camera_label: Label of camera to animate
        movement_type: Type of camera movement. Options:
            - "dolly-in": Move camera forward along its horizontal view direction
            - "dolly-out": Move camera backward
            - "pan-left": Turn camera left (horizontal)
            - "pan-right": Turn camera right (horizontal)
            - "tilt-up": Tilt camera up (vertical)
            - "tilt-down": Tilt camera down (vertical)
            - "crane-up": Move camera vertically upward
            - "crane-down": Move camera vertically downward
            - "handheld-shake": Repeatable procedural shake, keyed every 3 frames
        start_frame: Animation start frame (default: 0)
        end_frame: Animation end frame (default: 120)
        intensity: Movement amount multiplier 0.0-10.0 (default: 1.0)
            - dolly: 200cm * intensity; crane: 100cm * intensity
            - pan: 45 deg * intensity; tilt: 30 deg * intensity
            - shake: 5cm * intensity (rotation jitter half that, in degrees)

    Returns:
        Dict with:
        - camera: Camera label
        - movementType: Type of movement applied
        - keyframesSet: Number of camera keyframes created
        - frameRange: {start, end} frame range
        - description: Human-readable description of movement
        - intensity: Applied intensity value
        - endPosition: Camera position at end_frame

    Example:
        daz_animate_camera_movement("Camera 1", "dolly-in", 0, 180, intensity=1.0)
        daz_animate_camera_movement("Camera 1", "handheld-shake", 0, 300, intensity=0.3)
    """
    if not camera_label:
        raise ToolError("camera_label is required")
    if movement_type not in _CAMERA_MOVES:
        raise ToolError(
            f"Invalid movement_type '{movement_type}'. Valid options: {', '.join(_CAMERA_MOVES)}"
        )
    if start_frame < 0:
        raise ToolError("start_frame must be >= 0")
    if end_frame <= start_frame:
        raise ToolError(f"end_frame ({end_frame}) must be > start_frame ({start_frame})")
    if end_frame - start_frame > 10000:
        raise ToolError("Frame range too large (max 10000 frames)")
    if intensity < 0 or intensity > 10:
        raise ToolError("intensity must be between 0 and 10")
    kind, base = _CAMERA_MOVES[movement_type]
    amount = base * intensity

    def _run() -> dict[str, Any]:
        scene = get_scene()
        cam = _shots.camera(scene, camera_label)
        position, rotation = _shots.camera_pose(cam)
        shot = sl.camera_move(kind, position, rotation, start=start_frame, end=end_frame,
                              amount=amount, lens=Lens(focal_length=cam.focal_length or 50.0))
        apply_shot(scene, shot, camera=cam, clear_keys=False)
        keys = shot.movement.keyframes
        unit = " deg" if kind.startswith(("pan", "tilt")) else "cm"
        what = "amplitude " if kind == "handheld" else ""
        return {
            "camera": camera_label,
            "movementType": movement_type,
            "keyframesSet": len(keys),
            "frameRange": {"start": start_frame, "end": end_frame},
            "description": f"{movement_type.replace('-', ' ').capitalize()} ({what}{amount:.0f}{unit})",
            "intensity": intensity,
            "endPosition": _shots.vec(keys[-1].position),
        }

    return await _shots.run(_run)


@mcp.tool()
async def daz_create_camera_path(
    camera_label: str,
    waypoints: list[dict[str, Any]],
    easing: str = "smooth",
    aim_at_target: str | None = None,
) -> dict[str, Any]:
    """Create smooth camera path through multiple waypoints.

    Keys the camera at each waypoint as a ``dazpy.shots.Keyframed`` move;
    Studio interpolates between the keys. Existing position keys on the
    camera are cleared first (rotation keys too when aiming at a target).
    Perfect for tracking shots, reveals, and complex camera moves.

    Args:
        camera_label: Label of camera to animate
        waypoints: List of waypoint dicts, each containing:
            - position: Dict with x, y, z coordinates (world space, cm)
            - frame: Frame number for this waypoint
            Minimum 2 waypoints required. Automatically sorted by frame.
        easing: Requested interpolation: "linear", "smooth" (default),
            "ease-in" or "ease-out". Validated and echoed in the result only:
            Studio interpolates the keys with its default curve (dazpy has no
            per-key interpolation control yet). Add waypoints to shape the move.
        aim_at_target: Optional node label to track: the camera is aimed at
            it (a figure's eyes, a prop's centre) on every waypoint.

    Returns:
        Dict with:
        - camera: Camera label
        - waypointCount: Number of waypoints
        - easing: Easing type used
        - keyframesSet: Number of property keys set (3 per waypoint, 6 when aimed)
        - frameRange: {start, end} frame range
        - aimAtTarget: Target node label if specified; aimPoint: the point aimed at
        - shot: the applied shot (``dazpy.shots.Shot.to_dict()``)

    Example:
        # Simple 3-waypoint path
        daz_create_camera_path(
            "Camera 1",
            [
                {"position": {"x": 0, "y": 160, "z": 500}, "frame": 0},
                {"position": {"x": 200, "y": 180, "z": 300}, "frame": 90},
                {"position": {"x": 0, "y": 200, "z": 100}, "frame": 180}
            ],
            easing="smooth"
        )

        # Tracking shot following character
        daz_create_camera_path(
            "Camera 1",
            [
                {"position": {"x": -100, "y": 160, "z": 300}, "frame": 0},
                {"position": {"x": 100, "y": 160, "z": 300}, "frame": 120}
            ],
            aim_at_target="Genesis 9"
        )

        # Circular reveal
        import math
        radius = 300
        center_x, center_z = 0, 0
        waypoints = []
        for i in range(8):
            angle = (i / 8) * 2 * math.pi
            x = center_x + radius * math.sin(angle)
            z = center_z + radius * math.cos(angle)
            waypoints.append({
                "position": {"x": x, "y": 160, "z": z},
                "frame": i * 30
            })
        daz_create_camera_path("Camera 1", waypoints, easing="linear")

    Notes:
        - Waypoints are automatically sorted by frame; frames must be unique
        - Without aim_at_target the camera's rotation is left as it is
        - Use more waypoints for tighter curves
        - World space coordinates (same as daz_set_property)
        - Good for: dolly shots, crane shots, tracking shots, reveals
    """
    # Validate camera label
    if not camera_label:
        raise ToolError("camera_label is required")

    # Validate waypoints
    if not waypoints or len(waypoints) < 2:
        raise ToolError("At least 2 waypoints required")

    if len(waypoints) > 100:
        raise ToolError("Too many waypoints (max 100)")

    # Validate each waypoint
    for i, wp in enumerate(waypoints):
        if "position" not in wp:
            raise ToolError(f"Waypoint {i}: missing 'position' field")
        if "frame" not in wp:
            raise ToolError(f"Waypoint {i}: missing 'frame' field")

        pos = wp["position"]
        if not isinstance(pos, dict):
            raise ToolError(f"Waypoint {i}: position must be a dict")
        if "x" not in pos or "y" not in pos or "z" not in pos:
            raise ToolError(f"Waypoint {i}: position must have x, y, z fields")

        # Validate frame
        frame = wp["frame"]
        if not isinstance(frame, int) or frame < 0:
            raise ToolError(f"Waypoint {i}: frame must be a non-negative integer")

    # Validate easing
    valid_easing = ["linear", "smooth", "ease-in", "ease-out"]
    if easing not in valid_easing:
        raise ToolError(
            f"Invalid easing '{easing}'. "
            f"Valid options: {', '.join(valid_easing)}"
        )

    ordered = sorted(waypoints, key=lambda wp: wp["frame"])
    frames = [wp["frame"] for wp in ordered]
    if len(set(frames)) != len(frames):
        raise ToolError("Waypoint frames must be unique")

    def _run() -> dict[str, Any]:
        scene = get_scene()
        cam = _shots.camera(scene, camera_label)
        target = _shots.subject(scene, aim_at_target).focus_point if aim_at_target else None
        keys = tuple(
            CameraKeyframe(frame=wp["frame"], look_at=target,
                           position=Vec3(float(wp["position"]["x"]), float(wp["position"]["y"]),
                                         float(wp["position"]["z"])))
            for wp in ordered)
        first = keys[0]
        shot = Shot(id=sl.shot_name("move", aim_at_target, tag="path"),
                    camera=Placement(position=first.position, look_at=target),
                    lens=Lens(focal_length=cam.focal_length or 50.0),
                    movement=Keyframed(keyframes=keys), frame_range=(first.frame, keys[-1].frame))
        apply_shot(scene, shot, camera=cam)
        return {
            "camera": camera_label,
            "waypointCount": len(keys),
            "easing": easing,
            "keyframesSet": len(keys) * (6 if target is not None else 3),
            "frameRange": {"start": first.frame, "end": keys[-1].frame},
            "aimAtTarget": aim_at_target,
            "aimPoint": _shots.vec(target) if target is not None else None,
            "shot": shot.to_dict(),
        }

    return await _shots.run(_run)


# ---------------------------------------------------------------------------
# Character Choreography Tools (Phase 4.6)
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_create_character_path(
    character_label: str,
    waypoints: list[dict[str, Any]],
    path_type: str = "straight",
    walking_style: str = "casual",
) -> dict[str, Any]:
    """Animate character movement along a path with waypoints.

    Creates keyframe animation for character walking/moving through multiple positions.
    Character automatically rotates to face direction of travel.

    Args:
        character_label: Label of character to animate
        waypoints: List of waypoint dicts, each containing:
            - position: Dict with x, y, z coordinates (world space, cm)
            - frame: Frame number for this waypoint
            Minimum 2 waypoints required. Automatically sorted by frame.
        path_type: Type of path (currently visual only):
            - "straight": Straight line between waypoints
            - "curved": Curved path (future implementation)
            - "circular": Circular path (future implementation)
        walking_style: Walking animation style (informational):
            - "casual": Normal walking pace
            - "hurried": Fast walking
            - "sneaking": Slow, careful movement

    Returns:
        Dict with:
        - character: Character label
        - waypointCount: Number of waypoints
        - pathType: Path type used
        - walkingStyle: Walking style
        - keyframesSet: Number of keyframes created (position + rotation)
        - frameRange: {start, end} frame range
        - totalDistance: Total distance traveled (cm)
        - note: Reminder about walking cycle animation

    Example:
        # Simple straight path
        daz_create_character_path(
            "Genesis 9",
            [
                {"position": {"x": -200, "y": 0, "z": 0}, "frame": 0},
                {"position": {"x": 0, "y": 0, "z": 0}, "frame": 60},
                {"position": {"x": 200, "y": 0, "z": 0}, "frame": 120}
            ],
            walking_style="casual"
        )

        # Character walks across room
        daz_create_character_path(
            "Alice",
            [
                {"position": {"x": -300, "y": 0, "z": 100}, "frame": 0},
                {"position": {"x": 300, "y": 0, "z": 100}, "frame": 180}
            ],
            walking_style="hurried"
        )

    Notes:
        - Character automatically rotates to face direction of movement
        - Creates 3 position keyframes + 1 rotation keyframe per waypoint
        - Walking cycle animation must be applied separately
        - Use with animation poses for realistic walking motion
        - Y position can be animated for stairs/slopes
        - Total distance calculated for reference
        - For running: use shorter duration between waypoints
        - For sneaking: use longer duration between waypoints
    """
    # Validate character label
    if not character_label:
        raise ToolError("character_label is required")

    # Validate waypoints
    if not waypoints or len(waypoints) < 2:
        raise ToolError("At least 2 waypoints required")

    if len(waypoints) > 100:
        raise ToolError("Too many waypoints (max 100)")

    # Validate each waypoint
    for i, wp in enumerate(waypoints):
        if "position" not in wp:
            raise ToolError(f"Waypoint {i}: missing 'position' field")
        if "frame" not in wp:
            raise ToolError(f"Waypoint {i}: missing 'frame' field")

        pos = wp["position"]
        if not isinstance(pos, dict):
            raise ToolError(f"Waypoint {i}: position must be a dict")
        if "x" not in pos or "y" not in pos or "z" not in pos:
            raise ToolError(f"Waypoint {i}: position must have x, y, z fields")

        frame = wp["frame"]
        if not isinstance(frame, int) or frame < 0:
            raise ToolError(f"Waypoint {i}: frame must be a non-negative integer")

    # Validate path type
    valid_path_types = ["straight", "curved", "circular"]
    if path_type not in valid_path_types:
        raise ToolError(
            f"Invalid path_type '{path_type}'. "
            f"Valid options: {', '.join(valid_path_types)}"
        )

    # Validate walking style
    valid_styles = ["casual", "hurried", "sneaking"]
    if walking_style not in valid_styles:
        raise ToolError(
            f"Invalid walking_style '{walking_style}'. "
            f"Valid options: {', '.join(valid_styles)}"
        )

    return await _execute_by_id("vangard-create-character-path", {
        "characterLabel": character_label,
        "waypoints": waypoints,
        "pathType": path_type,
        "walkingStyle": walking_style,
    })


@mcp.tool()
async def daz_arrange_characters(
    characters: list[str],
    arrangement: str,
    spacing: float = 80.0,
    facing: str = "forward",
    center_position: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Position multiple characters in formation.

    Arranges characters in standard formations (line, semicircle, triangle, circle)
    with automatic positioning and rotation. Perfect for group shots and scenes.

    Args:
        characters: List of character labels (minimum 2)
        arrangement: Formation type:
            - "line": Straight line along X axis
            - "semicircle": Arc formation facing forward
            - "triangle": Triangular formation (2-3 chars: triangle, 4+: rows)
            - "conversation-circle": Circle facing inward
        spacing: Distance between characters in cm (default: 80)
        facing: Direction characters face:
            - "forward": All face +Z direction (camera at origin)
            - "center": All face formation center (for circle)
            - "camera": All face toward camera (same as forward)
        center_position: Optional center point for formation.
            Dict with x, y, z keys. Default: {x: 0, y: 0, z: 0}

    Returns:
        Dict with:
        - characters: List of dicts with label, position {x, y, z}, rotation
        - arrangement: Formation type used
        - spacing: Spacing value
        - facing: Facing direction
        - count: Number of characters arranged

    Example:
        # Line up 5 characters
        daz_arrange_characters(
            ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            arrangement="line",
            spacing=100,
            facing="forward"
        )

        # Semicircle for group portrait
        daz_arrange_characters(
            ["Person1", "Person2", "Person3", "Person4"],
            arrangement="semicircle",
            spacing=120,
            facing="forward"
        )

        # Conversation circle
        daz_arrange_characters(
            ["Alice", "Bob", "Charlie"],
            arrangement="conversation-circle",
            spacing=100,
            facing="center",
            center_position={"x": 0, "y": 0, "z": 200}
        )

        # Triangle formation
        daz_arrange_characters(
            ["Leader", "Left", "Right"],
            arrangement="triangle",
            spacing=90
        )

    Notes:
        - Formations centered at center_position (default: origin)
        - Line: Arranged left-to-right along X axis
        - Semicircle: Arc radius calculated from spacing and character count
        - Triangle: 2-3 chars form triangle, 4+ form two rows
        - Conversation-circle: All face inward at equal angles
        - Use larger spacing for formal arrangements
        - Use smaller spacing for intimate/crowded scenes
        - Spacing measured center-to-center between characters
        - Y position preserved from center_position (for platforms/stages)
    """
    # Validate characters
    if len(characters) > 20:
        raise ToolError("Too many characters (max 20)")

    if not characters:
        return {"characters": [], "arrangement": arrangement, "spacing": spacing,
                "facing": facing, "count": 0}

    # Validate arrangement — accept "circle" as alias for "conversation-circle"
    if arrangement == "circle":
        arrangement = "conversation-circle"
    valid_arrangements = ["line", "semicircle", "triangle", "conversation-circle"]
    if arrangement not in valid_arrangements:
        raise ToolError(
            f"Invalid arrangement '{arrangement}'. "
            f"Valid options: {', '.join(valid_arrangements)}"
        )

    # Validate spacing
    if spacing < 10 or spacing > 500:
        raise ToolError("spacing must be between 10 and 500 cm")

    # Validate facing
    valid_facing = ["forward", "center", "camera"]
    if facing not in valid_facing:
        raise ToolError(
            f"Invalid facing '{facing}'. "
            f"Valid options: {', '.join(valid_facing)}"
        )

    # Validate center_position
    center_pos = center_position or {"x": 0, "y": 0, "z": 0}
    if not isinstance(center_pos, dict):
        raise ToolError("center_position must be a dict")
    if "x" not in center_pos or "y" not in center_pos or "z" not in center_pos:
        raise ToolError("center_position must have x, y, z fields")

    return await _execute_by_id("vangard-arrange-characters", {
        "characters": characters,
        "arrangement": arrangement,
        "spacing": spacing,
        "facing": facing,
        "centerPosition": center_pos,
    })


@mcp.tool()
async def daz_choreograph_action(
    action_type: str,
    characters: list[str],
    start_frame: int = 0,
    duration: int = 90,
) -> dict[str, Any]:
    """Choreograph simple action between characters.

    Automatically positions characters for common interactions (handshake, hug,
    fight, dance) with appropriate spacing and facing. Provides suggestions for
    completing the choreography.

    Args:
        action_type: Type of action to choreograph:
            - "handshake": Business/friendly handshake (60cm apart)
            - "hug": Intimate embrace (30cm apart)
            - "fight": Combat stance (100cm apart)
            - "dance": Partner dance position (40cm apart)
        characters: List of character labels (requires 2 for all types)
        start_frame: Frame to start action (default: 0)
        duration: Length of action in frames (default: 90 = 3 seconds at 30fps)

    Returns:
        Dict with:
        - actionType: Type of action
        - characters: List of character labels
        - positions: List of dicts with character, position {x, y, z}, rotation
        - frameRange: {start, end} frame range
        - suggestions: List of recommended next steps

    Example:
        # Handshake between two business people
        result = daz_choreograph_action(
            "handshake",
            ["Alice", "Bob"],
            start_frame=0,
            duration=60
        )
        # Positions characters facing each other
        # Suggestions include using daz_reach_toward for hands

        # Emotional hug
        result = daz_choreograph_action(
            "hug",
            ["Mother", "Child"],
            start_frame=30,
            duration=120
        )
        # Positions very close, facing each other
        # Suggests using daz_interactive_pose for arms

        # Action fight scene
        result = daz_choreograph_action(
            "fight",
            ["Hero", "Villain"],
            start_frame=0,
            duration=180
        )
        # Positions at fighting distance
        # Suggests combat poses and angry emotions

        # Romantic dance
        result = daz_choreograph_action(
            "dance",
            ["Dancer1", "Dancer2"],
            start_frame=0,
            duration=240
        )
        # Positions for partner dance
        # Suggests dance poses and path animation

    Notes:
        - All actions require exactly 2 characters
        - Characters positioned facing each other
        - Spacing automatically determined by action type
        - Handshake: 60cm (arm's reach)
        - Hug: 30cm (intimate distance)
        - Fight: 100cm (combat distance)
        - Dance: 40cm (close dance position)
        - This is positioning only - use suggestions for complete choreography
        - Follow up with daz_reach_toward, daz_interactive_pose, or pose loading
        - Use daz_set_emotion for appropriate facial expressions
        - Use daz_create_character_path for dance movement
    """
    # Validate action type
    valid_actions = ["handshake", "hug", "fight", "dance"]
    if action_type not in valid_actions:
        raise ToolError(
            f"Invalid action_type '{action_type}'. "
            f"Valid options: {', '.join(valid_actions)}"
        )

    # Validate characters — require 2 for two-character actions, allow fewer as no-op
    if not characters:
        return {"actionType": action_type, "characters": [], "positions": [],
                "frameRange": {"start": start_frame, "end": start_frame + duration},
                "suggestions": ["Add 2 characters to the scene to use this tool"]}

    if len(characters) == 1:
        return {"actionType": action_type, "characters": characters, "positions": [],
                "frameRange": {"start": start_frame, "end": start_frame + duration},
                "suggestions": [
                    "Add a second character to the scene to choreograph a " + action_type
                ]}

    # Validate frame range
    if start_frame < 0:
        raise ToolError("start_frame must be >= 0")

    if duration < 10 or duration > 1000:
        raise ToolError("duration must be between 10 and 1000 frames")

    return await _execute_by_id("vangard-choreograph-action", {
        "actionType": action_type,
        "characters": characters,
        "startFrame": start_frame,
        "duration": duration,
    })


# ---------------------------------------------------------------------------
# Phase 4.7: Cinematic Coverage Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_setup_shot_coverage(
    subject_label: str,
    coverage_type: str = "standard",
    camera_height: float | None = None,
    auto_aim: bool = True,
) -> dict[str, Any]:
    """Create multiple camera angles for cinematic coverage of a subject.

    Builds the coverage with ``dazpy.shot_library.subject_coverage``: each
    camera frames the subject at its shot size, fitted to its lens, from the
    front (Genesis figures face +Z). Cameras are labelled with their shot ids.

    Args:
        subject_label: Label of subject node (character, prop, etc.)
        coverage_type: Type of coverage to set up:
            - "standard": Wide (35mm), Medium (50mm), Close-up (85mm)
            - "interview": Medium (50mm) + medium close-ups at -30 / +30 deg (85mm)
            - "dramatic": Wide, Low-angle medium, High-angle medium, Profile MCU
            - "action": Wide (28mm), Medium, Three-quarter medium-wide, Hero low
        camera_height: Optional aim height in cm above the subject's base for
            every shot. Default: each shot size's own aim height (eyes for a
            close-up, chest for a medium, mid-body for a wide).
        auto_aim: Kept for compatibility; cameras are always aimed at the subject.

    Returns:
        Dict with:
        - coverageType, subject, subjectPosition
        - cameras: list of {name, label, shotId, position, focalLength, size}
        - cameraCount
        - suggestions: recommended next steps

    Example:
        daz_setup_shot_coverage("Alice", coverage_type="interview")
    """
    del auto_aim  # always aimed
    valid_types = list(sl.COVERAGE_PRESETS)
    if coverage_type not in valid_types:
        raise ToolError(
            f"Invalid coverage_type '{coverage_type}'. Valid options: {', '.join(valid_types)}"
        )
    if camera_height is not None and (camera_height < 0 or camera_height > 500):
        raise ToolError("camera_height must be between 0 and 500 cm")

    def _run() -> dict[str, Any]:
        scene = get_scene()
        subj = _shots.subject(scene, subject_label)
        positions = {subject_label: subj.root}
        shots = list(sl.subject_coverage(subject_label, preset=coverage_type).all_shots())
        if camera_height is not None:
            shots = [replace(s, camera=replace(s.camera, anchor_cm=camera_height)) for s in shots]
        cams = sl.apply_coverage(scene, shots, subjects=positions)
        cameras = [{"name": label, **_shots.shot_summary(s, label, positions)}
                   for s, label in zip(shots, cams)]
        return {
            "coverageType": coverage_type,
            "subject": subject_label,
            "subjectPosition": _shots.vec(subj.root),
            "cameras": cameras,
            "cameraCount": len(cameras),
            "suggestions": [
                "Switch between cameras to render different angles",
                "Use daz_animate_camera_movement for dynamic shots",
                "Use daz_create_shot_sequence('shot-reverse-shot', ...) to cover a two-person scene",
            ],
        }

    return await _shots.run(_run)


_COVERAGE_PARTS = ("master", "two_shot", "ots", "singles")


def _conversation_beats(beats: list[dict[str, Any]],
                        speakers: tuple[str, str]) -> list[sl.DialogueBeat]:
    """Validate MCP beat dicts and turn them into ``DialogueBeat`` objects."""
    out: list[sl.DialogueBeat] = []
    for i, beat in enumerate(beats, start=1):
        missing = [k for k in ("speaker", "start", "end") if k not in beat]
        if missing:
            raise ToolError(f"Beat {i}: missing field(s) {missing}")
        start, end = beat["start"], beat["end"]
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start:
            raise ToolError(f"Beat {i}: start/end must be integers with 0 <= start <= end")
        if beat["speaker"] not in speakers:
            raise ToolError(f"Beat {i}: speaker {beat['speaker']!r} must be "
                            f"{speakers[0]!r} or {speakers[1]!r}")
        if out and start <= out[-1].end:
            raise ToolError(f"Beat {i} starts at frame {start}, "
                            f"before beat {i - 1} ends ({out[-1].end})")
        out.append(sl.DialogueBeat(beat["speaker"], start, end, beat.get("line")))
    return out


@mcp.tool()
async def daz_cover_conversation(
    char_a: str,
    char_b: str,
    beats: list[dict[str, Any]] | None = None,
    style: str = "ots",
    side: int = 1,
    establish_frames: int = 0,
    single_size: str = "medium-close-up",
    focal_length: float | None = None,
    include: list[str] | None = None,
) -> dict[str, Any]:
    """Cover or cut a two-person conversation, keeping every camera on one side of the line.

    Built on ``dazpy.shot_library``. Every camera stands on the same side of
    the line of action between the two characters (the 180-degree rule), so
    eyelines match across cuts. One camera is created per shot, labelled with
    its shot id.

    With ``beats``, the conversation is cut: one shot per beat on the speaker,
    over the listener's shoulder (``style="ots"``) or in a clean single
    (``style="singles"``), timed to the beat's frames, optionally opening on
    a master. Without ``beats``, standard coverage is set up instead: master,
    two-shot, the OTS pair and both clean singles (pick parts with ``include``).

    Args:
        char_a: Label of the first character.
        char_b: Label of the second character.
        beats: Dialogue beats in cut order, each
            ``{"speaker": char_a|char_b, "start": int, "end": int, "line": str?}``
            (frames inclusive; a beat must start after the previous one ends).
        style: "ots" (default) or "singles" -- how each beat frames the speaker.
        side: Which side of the line the cameras stand on: 1 (default) =
            char_a's right as they face char_b, -1 = the other side.
        establish_frames: With beats, open on a master for this many frames
            at the start of the first beat (0 = no master).
        single_size: Shot size of the clean singles: "extreme-close-up",
            "close-up", "medium-close-up" (default), "medium-shot",
            "medium-full", "full-shot", "wide-shot", "extreme-wide".
        focal_length: Lens in mm for the beat shots (default: each shot's own).
        include: Without beats, the coverage parts to create, from
            "master", "two_shot", "ots", "singles" (default: all).

    Returns:
        Dict with:
        - mode: "conversation" (beats given) or "coverage"
        - planId, characters, side
        - cameras: list of {label, shotId, position, focalLength, frameRange?, size?}
        - cutList: with beats, the edit in order -- {shot, camera, start, end,
          speaker?, line?} (speaker is absent on the establishing master)
        - continuity: line-crossing issues, plus jump cuts (< 30 degrees at a
          similar size) between consecutive beats of a conversation

    Example:
        daz_cover_conversation("Alice", "Bob", beats=[
            {"speaker": "Alice", "start": 0, "end": 59, "line": "You came back."},
            {"speaker": "Bob", "start": 60, "end": 119, "line": "I had to."},
        ], establish_frames=24)
        # 000_MST_Alice-Bob (0-23), 001_OTS_Alice_over_Bob (24-59),
        # 002_OTS_Bob_over_Alice (60-119)

        daz_cover_conversation("Alice", "Bob")   # master, two-shot, OTS pair, singles
    """
    if not char_a or not char_b or char_a == char_b:
        raise ToolError("char_a and char_b must be two different character labels")
    if style not in ("ots", "singles"):
        raise ToolError("style must be 'ots' or 'singles'")
    if side not in (1, -1):
        raise ToolError("side must be 1 or -1")
    if establish_frames < 0:
        raise ToolError("establish_frames must be >= 0")
    if single_size not in _shots.SHOT_TYPES:
        raise ToolError(f"single_size must be one of: {', '.join(_shots.SHOT_TYPES)}")
    if focal_length is not None and not 10.0 <= focal_length <= 500.0:
        raise ToolError("focal_length must be between 10 and 500 mm")
    parts = tuple(include) if include else _COVERAGE_PARTS
    bad_parts = sorted(set(parts) - set(_COVERAGE_PARTS))
    if bad_parts:
        raise ToolError(f"Unknown include part(s) {bad_parts}; valid: {', '.join(_COVERAGE_PARTS)}")
    dialogue = _conversation_beats(beats, (char_a, char_b)) if beats else None
    size = _shots.SHOT_TYPES[single_size]

    def _run() -> dict[str, Any]:
        scene = get_scene()
        positions = {n: _shots.subject(scene, n).root for n in (char_a, char_b)}
        line = sl.LineOfAction.between(positions, char_a, char_b, side)
        if dialogue:
            plan = sl.conversation(line, dialogue, plan_id=f"{char_a}_{char_b}_conversation",
                                   style=style, establish_frames=establish_frames,
                                   single_size=size, lens=focal_length)
            # Shots are in cut order: check the axis and jump cuts between beats.
            continuity = sl.check_plan(plan, positions)
        else:
            plan = sl.dialogue_coverage(line, include=parts, single_size=size)
            # Coverage setups are alternatives, not a cut: only the axis applies.
            continuity = sl.check_axis(plan.all_shots(), sl.plan_line(plan, positions), positions)
        shots = list(plan.all_shots())
        cams = sl.apply_coverage(scene, plan, subjects=positions)
        result: dict[str, Any] = {
            "mode": "conversation" if dialogue else "coverage",
            "planId": plan.id,
            "characters": [char_a, char_b],
            "side": side,
            "cameras": [_shots.shot_summary(s, label, positions) for s, label in zip(shots, cams)],
            "continuity": _shots.issues(continuity),
        }
        if dialogue:
            cut_list = []
            for s, label in zip(shots, cams):
                entry: dict[str, Any] = {"shot": s.id, "camera": label,
                                         "start": s.frame_range[0], "end": s.frame_range[1]}
                if s.gaze:
                    entry["speaker"] = s.gaze[0].actor
                if s.storyboard is not None and s.storyboard.dialogue:
                    entry["line"] = s.storyboard.dialogue
                cut_list.append(entry)
            result["cutList"] = cut_list
        return result

    return await _shots.run(_run)


@mcp.tool()
async def daz_create_camera_rig(
    rig_name: str = "CameraRig",
    center_position: dict[str, float] | None = None,
    camera_count: int = 3,
    radius: float = 250.0,
    height_variation: float = 40.0,
    focal_lengths: list[int] | None = None,
) -> dict[str, Any]:
    """Set up multi-camera rig for bullet-time or simultaneous multi-angle shots.

    Creates multiple cameras arranged in a circle around a center point, each
    aimed at the centre (``dazpy.shots.Placement`` shots applied with
    ``dazpy.shot_library.apply_coverage``), all parented to a rig controller
    group node. Rotate the rig to orbit all cameras around the subject, or
    switch between cameras for instant angle changes. Running it again with
    the same rig_name re-aims the existing cameras and rig instead of
    duplicating them.

    Args:
        rig_name: Base name for rig (default: "CameraRig")
        center_position: Center point {x, y, z} in cm (default: {x:0, y:150, z:0})
        camera_count: Number of cameras in rig, 2-8 (default: 3)
        radius: Distance from center to cameras in cm (default: 250)
        height_variation: Variation in camera heights in cm (default: 40)
        focal_lengths: List of focal lengths in mm (default: [35, 50, 85])

    Returns:
        Dict with:
        - rigName: Name of rig
        - rigLabel: Label of rig parent node
        - centerPosition: {x, y, z} center point
        - radius: Distance from center
        - cameraCount: Number of cameras
        - cameras: List of dicts with name, label, angle, focalLength,
          heightOffset, position (world), reused
        - suggestions: List of recommended next steps

    Example:
        # 3-camera rig for product visualization
        result = daz_create_camera_rig(
            rig_name="ProductRig",
            center_position={"x": 0, "y": 100, "z": 0},
            camera_count=3,
            radius=200,
            focal_lengths=[50, 50, 50]
        )
        # Creates 3 cameras at 120° intervals, all 200cm from center

        # 8-camera bullet-time rig
        result = daz_create_camera_rig(
            rig_name="BulletTime",
            center_position={"x": 0, "y": 150, "z": 0},
            camera_count=8,
            radius=300,
            height_variation=20,
            focal_lengths=[85, 85, 85, 85, 85, 85, 85, 85]
        )
        # Creates 8 cameras at 45° intervals for smooth frozen-time effect

        # 4-camera interview rig with varied focal lengths
        result = daz_create_camera_rig(
            rig_name="InterviewRig",
            camera_count=4,
            radius=250,
            focal_lengths=[35, 50, 85, 85]
        )
        # Wide, medium, two closeups at different angles

    Notes:
        - All cameras parented to rig controller node
        - Rotate rig YRotate to orbit all cameras around subject
        - Animate rig position to move entire camera array
        - Switch between cameras for instant angle changes (bullet-time)
        - Height variation adds subtle vertical offsets for visual interest
          (camera i is raised by sin(0.7 * i) * height_variation)
        - Cameras point at center; angle 0 is the centre's +Z side
        - If focal_lengths list too short, remaining cameras use 50mm
        - Cameras named RigName_Cam1, RigName_Cam2, etc.
        - Evenly spaced around circle (360° / camera_count)
        - Perfect for:
          * Bullet-time effects (8+ cameras)
          * Product turntables (3-4 cameras)
          * Multi-angle coverage (4-6 cameras)
          * 360° video (6-8 cameras)
    """
    # Validate camera count
    if camera_count < 2 or camera_count > 8:
        raise ToolError("camera_count must be between 2 and 8")

    # Validate radius
    if radius < 50 or radius > 2000:
        raise ToolError("radius must be between 50 and 2000 cm")

    # Validate height variation
    if height_variation < 0 or height_variation > 200:
        raise ToolError("height_variation must be between 0 and 200 cm")

    # Default center position
    if center_position is None:
        center_position = {"x": 0.0, "y": 150.0, "z": 0.0}

    # Default focal lengths
    if focal_lengths is None:
        focal_lengths = [35, 50, 85]

    # Validate focal lengths
    if focal_lengths:
        for fl in focal_lengths:
            if fl < 10 or fl > 200:
                raise ToolError("All focal lengths must be between 10 and 200 mm")

    for key in ("x", "y", "z"):
        if key not in center_position:
            raise ToolError("center_position must have x, y, z fields")
    lenses = [float(f) for f in focal_lengths] + [50.0] * max(0, camera_count - len(focal_lengths))
    center = Vec3(float(center_position["x"]), float(center_position["y"]),
                  float(center_position["z"]))

    def _run() -> dict[str, Any]:
        scene = get_scene()
        shots, info = [], []
        for i in range(camera_count):
            azimuth = i * 360.0 / camera_count
            height = math.sin(i * 0.7) * height_variation
            elevation = math.degrees(math.atan2(height, radius))
            position = _shots.orbit_position(center, azimuth, elevation, math.hypot(radius, height))
            shots.append(Shot(id=f"{rig_name}_Cam{i + 1}", lens=Lens(focal_length=lenses[i]),
                              camera=Placement(position=position, look_at=center)))
            info.append((azimuth, height))
        existing = {s.id: c for s in shots if (c := _shots.find_camera(scene, s.id)) is not None}
        cams = sl.apply_coverage(scene, shots, cameras=existing)
        rig = _shots.group_node(scene, f"{rig_name}_Rig", center)
        for cam in cams.values():
            cam.reparent(rig, preserve_world_transform=True)
        return {
            "rigName": rig_name,
            "rigLabel": f"{rig_name}_Rig",
            "centerPosition": _shots.vec(center),
            "radius": radius,
            "cameraCount": camera_count,
            "cameras": [{"name": s.id, "label": s.id, "angle": round(az, 1),
                         "focalLength": s.lens.focal_length, "heightOffset": round(h, 1),
                         "position": _shots.vec(s.camera.position),
                         "reused": s.id in existing}
                        for s, (az, h) in zip(shots, info)],
            "suggestions": [
                f"Rotate {rig_name}_Rig's YRotate to orbit every camera around the centre",
                "Animate the rig's translation to move the whole array",
                "Switch cameras with daz_set_active_camera for instant angle changes",
            ],
        }

    return await _shots.run(_run)


# ---------------------------------------------------------------------------
# Phase 4.8: Lighting Animation tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_animate_light(
    light_label: str,
    movement_type: str = "flicker",
    start_frame: int = 0,
    end_frame: int = 90,
    intensity: float = 1500.0,
    flicker_amount: float = 0.3,
    strobe_interval: int = 5,
    pulse_count: int = 3,
) -> dict:
    """Animate a light's intensity over a frame range with a named effect pattern.

    Adds keyframes to a light's Flux (intensity) property to create dynamic
    lighting effects. The light must already exist in the scene.

    Args:
        light_label: Label of the light node in the scene (e.g. "Spot Light 1").
        movement_type: Effect pattern — one of:
            - "flicker": Random intensity variation (fire, candle, bad wiring)
            - "pulse": Smooth sine-wave pulsing (breathing light, heartbeat)
            - "fade-in": Ramp from 0 to target intensity over the frame range
            - "fade-out": Ramp from target intensity to 0 over the frame range
            - "strobe": Hard on/off alternation at regular intervals
            - "color-cycle": Animate color temperature warm→cool→warm
        start_frame: First frame of the animation range (default 0).
        end_frame: Last frame of the animation range (default 90 = 3 sec at 30fps).
        intensity: Target flux (lumens) for full brightness (default 1500).
        flicker_amount: Fraction of intensity to vary (0.0–1.0, default 0.3 = ±30%).
            Used by "flicker" and "pulse" modes.
        strobe_interval: Frames between each on/off switch for "strobe" mode (default 5).
        pulse_count: Number of full pulse cycles for "pulse" mode (default 3).

    Returns:
        dict with keys: light, movementType, startFrame, endFrame, targetIntensity,
        keyframesCreated (count), keyframes (list of {frame, value}), suggestions.

    Examples:
        # Candle flicker over 5 seconds
        result = daz_animate_light(
            "Point Light 1", movement_type="flicker",
            start_frame=0, end_frame=149, intensity=800, flicker_amount=0.4
        )

        # Dramatic fade-in (lights come up over 2 seconds)
        result = daz_animate_light(
            "Spot Light 1", movement_type="fade-in",
            start_frame=0, end_frame=59, intensity=5000
        )

        # Police strobe effect
        result = daz_animate_light(
            "Spot Light 2", movement_type="strobe",
            start_frame=0, end_frame=90, intensity=10000, strobe_interval=3
        )

        # Breathing heartbeat pulse (3 pulses over 4 seconds)
        result = daz_animate_light(
            "Rim Light", movement_type="pulse",
            start_frame=0, end_frame=119, intensity=2000, pulse_count=3
        )

    Notes:
        - All keyframes are added to the light's Flux property
        - "color-cycle" attempts Color/Red, Color/Green, Color/Blue properties;
          falls back to constant flux if color channels not found
        - Existing keyframes on the Flux property are NOT cleared first —
          use daz_clear_animation beforehand if needed
        - Use daz_set_frame_range to ensure timeline covers start_frame to end_frame
        - Combine with daz_animate_camera_movement for cinematic lighting + camera animation
    """
    if movement_type not in ("flicker", "pulse", "fade-in", "fade-out", "strobe", "color-cycle"):
        raise ToolError(
            f"Invalid movement_type '{movement_type}'. "
            "Valid: flicker, pulse, fade-in, fade-out, strobe, color-cycle"
        )
    if start_frame < 0 or end_frame <= start_frame:
        raise ToolError("start_frame must be >= 0 and end_frame must be > start_frame")
    if intensity < 0 or intensity > 100000:
        raise ToolError("intensity must be between 0 and 100000 lumens")
    if not 0.0 <= flicker_amount <= 1.0:
        raise ToolError("flicker_amount must be between 0.0 and 1.0")
    if strobe_interval < 1:
        raise ToolError("strobe_interval must be at least 1 frame")
    if pulse_count < 1:
        raise ToolError("pulse_count must be at least 1")

    result = await run_tool(lambda: _lighting.animate_light(
        light_label, movement_type, start_frame, end_frame, intensity, flicker_amount,
        strobe_interval, pulse_count))
    result["suggestions"] = [
        "Use daz_render_animation to render the lighting animation",
        "Combine with daz_animate_camera_movement for cinematic effect",
        "Layer multiple lights with offset timing for rich atmosphere",
    ]
    return result


@mcp.tool()
async def daz_create_light_sequence(
    sequence_type: str = "day-to-night",
    subject_label: str | None = None,
    start_frame: int = 0,
    end_frame: int = 120,
    create_lights: bool = True,
) -> dict:
    """Create an animated multi-light sequence for a cinematic mood or time-of-day.

    Sets up named lights with keyframed Flux values to simulate a complete
    lighting environment that evolves over time. If the named lights already
    exist in the scene they are reused; otherwise new lights are created
    (when create_lights=True).

    Args:
        sequence_type: Lighting scenario — one of:
            - "day-to-night": Bright daylight → warm sunset → dark night (3 lights)
            - "night-to-dawn": Dark night → pre-dawn glow → sunrise (2 lights)
            - "interrogation": Harsh overhead build with reveal spot (2 lights)
            - "romantic": Warm candlelight flicker + soft fill (2 lights)
            - "action-tension": Key + rim + climax flash (3 lights)
        subject_label: Optional scene node label to aim lights at. If provided,
            lights created by this tool will be aimed at the subject.
        start_frame: First frame of the sequence (default 0).
        end_frame: Last frame of the sequence (default 120 = 4 sec at 30fps).
        create_lights: If True (default), create lights that don't exist yet.
            If False, only animate lights that are already in the scene.

    Returns:
        dict with keys: sequenceType, startFrame, endFrame, lightsCreated (list),
        totalKeyframes, keyframes (list), suggestions.

    Examples:
        # Full day-to-night transition over 10 seconds
        result = daz_create_light_sequence(
            sequence_type="day-to-night",
            start_frame=0, end_frame=299
        )
        # Creates/animates: Sun_Key (8000→0 lux), Sky_Fill (2000→100)

        # Romantic candlelight scene
        result = daz_create_light_sequence(
            sequence_type="romantic",
            subject_label="Genesis 9",
            start_frame=0, end_frame=180
        )
        # Creates: Candle_Key (flickering 800 lux), Soft_Fill (400 lux constant)

        # Action scene climax with flash
        result = daz_create_light_sequence(
            sequence_type="action-tension",
            start_frame=0, end_frame=90
        )
        # Creates: Action_Key, Action_Rim, Flash_Light (10,000+ lux at climax)

        # Interrogation with growing tension
        result = daz_create_light_sequence(
            sequence_type="interrogation",
            subject_label="Suspect",
            start_frame=0, end_frame=150
        )
        # Creates: Overhead_Key (2000→5000 lux), Reveal_Spot (0→3000 at 75%)

    Notes:
        - Light names are fixed per sequence (e.g. "Sun_Key", "Candle_Key") so
          calling this tool twice will animate the same lights
        - Lights are created at default positions — position them manually or
          with daz_orbit_camera_around / daz_apply_lighting_preset afterward
        - Combine with daz_animate_camera_movement for full cinematic sequences
        - Use daz_render_animation to export the animated sequence
        - "romantic" candle uses random flicker — values will differ each call
    """
    if sequence_type not in (
        "day-to-night", "night-to-dawn", "interrogation", "romantic", "action-tension"
    ):
        raise ToolError(
            f"Invalid sequence_type '{sequence_type}'. "
            "Valid: day-to-night, night-to-dawn, interrogation, romantic, action-tension"
        )
    if start_frame < 0 or end_frame <= start_frame:
        raise ToolError("start_frame must be >= 0 and end_frame must be > start_frame")

    result = await run_tool(lambda: _lighting.light_sequence(
        sequence_type, start_frame, end_frame, create_lights))
    result["suggestions"] = [
        "Position lights in scene before rendering",
        "Use daz_render_animation to render the full sequence",
        "Adjust Flux values with daz_set_keyframe to fine-tune timing",
    ]
    return result


# ---------------------------------------------------------------------------
# Phase 4.9: Shot Planning tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_plan_shot(
    shot_type: str = "medium-shot",
    subject_label: str | None = None,
    camera_label: str | None = None,
    mood: str = "neutral",
    composition_rule: str = "rule-of-thirds",
) -> dict:
    """Analyse the current scene and return a concrete shot plan with camera, lighting,
    and character placement recommendations.

    No changes are made to the scene — this is a pure planning / advisory tool.
    It reads scene state (figure positions, existing cameras/lights), builds the
    shot with ``dazpy.shot_library`` and returns it (``shot``: a
    ``dazpy.shots.Shot`` dict, ready for ``apply_shot`` or a scene recipe)
    with a step-by-step action plan and recommended tool calls.

    Args:
        shot_type: Cinematic shot size — one of:
            "extreme-close-up", "close-up", "medium-close-up", "medium-shot",
            "medium-full", "full-shot", "wide-shot", "extreme-wide",
            "two-shot", "over-shoulder"
        subject_label: Scene node label for the primary subject (figure or prop).
            Framed as a standing figure at its root. If omitted, a figure
            standing at the scene origin is assumed. "two-shot" and
            "over-shoulder" pair the subject with the nearest other figure
            (the OTS looks over that figure's shoulder onto the subject).
        camera_label: Existing camera to use for recommendation context. If provided,
            tool call suggestions reference this camera by name.
        mood: Emotional tone that drives the lighting recommendation — one of:
            "neutral", "dramatic", "happy", "sad", "tense", "romantic",
            "horror", "action"
        composition_rule: Where the subject sits in frame — one of:
            "rule-of-thirds" (right third), "center-frame", "golden-ratio"
            (right golden section), "leading-lines" (left third, low angle).
            The camera turns; it does not move.

    Returns:
        dict with keys:
        - shotType, shotDescription, mood, compositionRule
        - subject, camera
        - sceneState: {numCameras, numLights, numSkeletons, figures[]}
        - recommendations:
            - camera: {position, aim, focalLength, distanceFromSubject (to the aim
                       point), horizontalAngle (0 = subject's +Z front),
                       verticalAngle (degrees above the aim), steps[]}
            - lighting: {preset, keyFlux, fillFlux, rimFlux, keyAngle, notes, steps[]}
            - character: {steps[]}
            - toolSequence: ordered list of suggested tool calls to execute
        - shot: the planned shot (``dazpy.shots.Shot.to_dict()``)

    Examples:
        # Plan a dramatic close-up
        plan = daz_plan_shot(
            shot_type="close-up",
            subject_label="Genesis 9",
            camera_label="Camera 1",
            mood="dramatic"
        )
        # Returns exact camera position, 85mm focal length, rembrandt lighting config

        # Plan a wide establishing shot
        plan = daz_plan_shot(
            shot_type="wide-shot",
            subject_label="Alice",
            mood="happy",
            composition_rule="rule-of-thirds"
        )

        # Plan a tense over-shoulder
        plan = daz_plan_shot(
            shot_type="over-shoulder",
            subject_label="Bob",
            mood="tense"
        )

    Notes:
        - No scene changes are made; this is a read-only advisory call
        - Sizes fit the shot type's default lens (24mm wide ... 100mm extreme
          close-up); the camera stands on the subject's front (+Z) side
        - Lighting flux values assume Iray renderer; adjust for other renderers
        - toolSequence contains copy-pasteable tool call strings with real values
        - Follow up with daz_apply_lighting_preset, daz_orbit_camera_around, etc.
    """
    if shot_type not in _VALID_SHOT_TYPES:
        raise ToolError(
            f"Invalid shot_type '{shot_type}'. "
            f"Valid: {', '.join(sorted(_VALID_SHOT_TYPES))}"
        )
    if mood not in _VALID_MOODS:
        raise ToolError(
            f"Invalid mood '{mood}'. "
            f"Valid: {', '.join(sorted(_VALID_MOODS))}"
        )
    if composition_rule not in _VALID_COMPOSITION_RULES:
        raise ToolError(
            f"Invalid composition_rule '{composition_rule}'. "
            f"Valid: {', '.join(sorted(_VALID_COMPOSITION_RULES))}"
        )

    def _run() -> dict[str, Any]:
        scene = get_scene()
        overview = scene.overview()
        positions = _shots.figure_positions(scene)
        if subject_label:
            subj = _shots.subject(scene, subject_label)
            key = subject_label
            positions[key] = subj.root
        else:
            key = "origin"
            positions[key] = Vec3(0.0, 0.0, 0.0)
        partner = _shots.nearest(positions, key) if shot_type in _shots.PAIR_TYPES else None
        screen_x, elevation, comp_note = _PLAN_COMPOSITION[composition_rule]
        composition = {sl.THIRD_X: "right_third", -sl.THIRD_X: "left_third"}.get(screen_x, "center")
        shot = _shots.size_shot(shot_type, key, positions, partner=partner, elevation=elevation,
                                composition=composition)
        position, aim = _shots.pose(shot, positions)
        if screen_x == sl.GOLDEN_X and shot_type not in _shots.PAIR_TYPES:
            aim = sl.compose_aim(position, aim, screen_x, shot.lens.focal_length)
            shot = Shot(id=shot.id, lens=shot.lens,
                        camera=Placement(position=position, look_at=aim))
        root = positions[key]
        azimuth, horizontal = _shots.horizontal_view(position, root, minimum=1.0)
        vertical = math.degrees(math.atan2(position.y - aim.y, max(horizontal, 1e-6)))
        light = _PLAN_MOODS[mood]
        key_flux = light["keyFlux"]
        fill_flux = round(key_flux * light["fillRatio"])
        rim_flux = round(key_flux * light["rimRatio"])
        focal = shot.lens.focal_length
        p = _shots.vec(position, 0)
        cam_name = camera_label or "<camera>"
        camera_steps = [
            f"Position camera at X={p['x']:.0f} Y={p['y']:.0f} Z={p['z']:.0f}",
            f"Set focal length to {focal:g}mm",
            f"Aim camera at X={aim.x:.0f} Y={aim.y:.0f} Z={aim.z:.0f}",
            comp_note,
        ]
        if partner:
            camera_steps.append(f"Partner for the {shot_type}: {partner}")
        if shot_type == "two-shot":
            char_steps = ["Place characters 60-80 cm apart facing each other or 3/4 to camera",
                          "Ensure both figures share equal frame space"]
            if partner is None:
                char_steps.insert(
                    0, "No second figure in the scene: planned as a medium-wide single")
        elif shot_type == "over-shoulder":
            char_steps = [f"Foreground: {partner}'s shoulder frames the near edge" if partner
                          else "No second figure: planned over the subject's own shoulder",
                          "Offset subjects horizontally so the background face is clear"]
        else:
            char_steps = ["Position subject at the desired world position",
                          "Genesis figures face +Z; the camera stands on that side at angle 0"]
        tools: list[str] = []
        if subject_label and shot_type in _shots.SHOT_TYPES:
            tools.append(f'daz_frame_shot("{cam_name}", "{subject_label}", "{shot_type}")')
            if composition_rule != "center-frame":
                tools.append(f'daz_apply_composition_rule("{cam_name}", "{subject_label}", '
                             f'"{composition_rule}")')
        elif subject_label and partner:
            tools.append(f'daz_create_shot_sequence("shot-reverse-shot", ["{subject_label}", '
                         f'"{partner}"])')
        else:
            tools.append(f'daz_set_property("{cam_name}", "XTranslate", {p["x"]:.0f})  # etc.')
        tools.append(f'daz_apply_lighting_preset("{light["preset"]}"'
                     + (f', "{subject_label}"' if subject_label else "") + ")")
        return {
            "shotType": shot_type,
            "shotDescription": _PLAN_DESCRIPTIONS[shot_type],
            "mood": mood,
            "compositionRule": composition_rule,
            "subject": subject_label,
            "camera": camera_label,
            "sceneState": {
                "numCameras": len(overview.get("cameras", [])),
                "numLights": len(overview.get("lights", [])),
                "numSkeletons": len(overview.get("figures", [])),
                "figures": [{"label": k, "position": _shots.vec(v)} for k, v in positions.items()
                            if k != "origin" or subject_label == "origin"],
            },
            "recommendations": {
                "camera": {
                    "position": p,
                    "aim": _shots.vec(aim, 0),
                    "focalLength": focal,
                    "distanceFromSubject": round(position.distance(aim), 1),
                    "horizontalAngle": round(azimuth, 1),
                    "verticalAngle": round(vertical, 1),
                    "steps": camera_steps,
                },
                "lighting": {
                    "preset": light["preset"], "keyFlux": key_flux, "fillFlux": fill_flux,
                    "rimFlux": rim_flux, "keyAngle": light["keyAngle"], "notes": light["notes"],
                    "steps": [
                        "Set environment mode to Scene Only (daz_set_property on Environment node)",
                        f"Key light: {light['keyAngle']} deg from the camera axis, "
                        f"Flux={key_flux} lm",
                        f"Fill light: opposite side, Flux={fill_flux} lm",
                        f"Rim light: behind the subject, Flux={rim_flux} lm",
                    ],
                },
                "character": {"steps": char_steps},
                "toolSequence": tools,
            },
            "shot": shot.to_dict(),
        }

    return await _shots.run(_run)


@mcp.tool()
async def daz_create_storyboard(
    title: str,
    shots: list[dict],
    start_frame: int = 0,
    frames_per_shot: int = 90,
    save_presets: bool = True,
) -> dict:
    """Generate a multi-shot storyboard: creates a named camera for each shot,
    positions it according to shot type, and returns a complete shot list with
    frame ranges and metadata.

    Each shot is built with ``dazpy.shot_library`` and, when save_presets=True,
    applied to its own camera node. The returned data includes frame ranges
    for the full timeline, per-shot details, and the whole board as a
    ``dazpy.shots.Sequence`` dict (``sequence``) whose shots carry their frame
    range and storyboard text.

    Args:
        title: Name for this storyboard (used as camera name prefix).
        shots: List of shot definition dicts. Each dict may contain:
            - shotType (str): One of the standard shot sizes (default "medium-shot").
                Valid: "extreme-close-up", "close-up", "medium-close-up",
                "medium-shot", "medium-full", "full-shot", "wide-shot",
                "extreme-wide", "two-shot", "over-shoulder"
            - label (str): Human-readable shot name (e.g. "Scene 1 - Establishing").
            - subjectLabel (str): Scene node to frame (default: a figure at the origin).
            - partnerLabel (str): Second figure for "two-shot" / "over-shoulder"
              (the OTS looks over the partner's shoulder onto the subject).
              Default: the figure nearest the subject.
            - cameraLabel (str): Override camera node name (default: title_Cam1, etc.).
            - durationFrames (int): Shot length in frames (default: frames_per_shot).
            - focalLength (int): Override focal length in mm.
            - distance (int): Override camera-to-subject distance in cm.
            - angle (int): Camera azimuth in degrees around the subject
              (0 = the subject's +Z front, 90 = its +X side).
            - description (str): Scene description / visual note.
            - action (str): Character action description.
            - dialogue (str): Spoken dialogue for this shot.
            - notes (str): Free-form notes.
            snake_case keys (shot_type, subject, partner, camera, duration,
            focal_length) are accepted too.
        start_frame: First frame of the storyboard timeline (default 0).
        frames_per_shot: Default frame count when durationFrames is not specified
            per shot (default 90 = 3 seconds at 30fps).
        save_presets: If True (default), create a camera node in the scene for
            each shot. If False, return planning data only without scene changes.

    Returns:
        dict with keys: title, totalShots, totalFrames, totalSeconds,
        startFrame, endFrame, shots[], cameras[] (labels of applied cameras),
        sequence (``Sequence.to_dict()``), suggestions[].
        Each shot entry contains: shotNumber, shotId, label, shotType, subject,
        camera, cameraCreated, applied, position, focalLength, distance (to the
        aim point), angle, startFrame, endFrame, durationFrames,
        durationSeconds, description, action, dialogue.

    Examples:
        # 3-shot dialogue scene
        result = daz_create_storyboard(
            title="Cafe Scene",
            shots=[
                {
                    "label": "Establishing",
                    "shotType": "wide-shot",
                    "subjectLabel": "Alice",
                    "durationFrames": 60,
                    "description": "Cafe interior, Alice enters"
                },
                {
                    "label": "Alice CU",
                    "shotType": "close-up",
                    "subjectLabel": "Alice",
                    "durationFrames": 90,
                    "dialogue": "I can't believe you're here."
                },
                {
                    "label": "Bob Reaction",
                    "shotType": "medium-close-up",
                    "subjectLabel": "Bob",
                    "durationFrames": 75,
                    "action": "Bob turns, surprised"
                }
            ]
        )
        # Creates 3 cameras: Cafe Scene_Cam1/2/3
        # Timeline: frames 0-224 (7.5 seconds)

        # Action sequence with mixed shot sizes
        result = daz_create_storyboard(
            title="Fight",
            shots=[
                {"label": "Wide", "shotType": "wide-shot", "durationFrames": 30},
                {"label": "Impact", "shotType": "extreme-close-up",
                 "subjectLabel": "Hero", "angle": 45, "durationFrames": 15},
                {"label": "Recovery", "shotType": "medium-shot",
                 "subjectLabel": "Hero", "durationFrames": 60}
            ],
            frames_per_shot=30
        )

    Notes:
        - Maximum 20 shots per storyboard
        - Camera nodes are named <title>_Cam1, _Cam2, etc. unless overridden
        - If a camera with the same label already exists, it is reused and re-aimed
        - Frame ranges are contiguous: shot N+1 starts at shot N's endFrame + 1
        - Use the suggestions[3] string to set the timeline range before rendering
        - Combine with daz_create_shot_sequence for automatic multi-camera coverage
    """
    if not shots:
        raise ToolError("shots list must not be empty")
    if len(shots) > 20:
        raise ToolError("Maximum 20 shots per storyboard")
    if start_frame < 0:
        raise ToolError("start_frame must be >= 0")
    if frames_per_shot < 1:
        raise ToolError("frames_per_shot must be at least 1")

    specs = []
    for i, raw in enumerate(shots):
        spec = {_STORYBOARD_ALIASES.get(k, k): v for k, v in raw.items()}
        st = spec.get("shotType", "medium-shot")
        if st not in _VALID_SHOT_TYPES:
            raise ToolError(
                f"Shot {i + 1} has invalid shotType '{st}'. "
                f"Valid: {', '.join(sorted(_VALID_SHOT_TYPES))}"
            )
        duration = spec.get("durationFrames") or frames_per_shot
        if not isinstance(duration, int) or duration < 1:
            raise ToolError(f"Shot {i + 1}: durationFrames must be a positive integer")
        specs.append({**spec, "shotType": st, "durationFrames": duration})

    def _run() -> dict[str, Any]:
        scene = get_scene()
        figures: dict[str, Vec3] | None = None
        positions: dict[str, Vec3] = {}
        built: list[tuple[Shot, str, dict[str, Any]]] = []
        frame = start_frame
        for i, spec in enumerate(specs, start=1):
            st, subj_label = spec["shotType"], spec.get("subjectLabel")
            if subj_label:
                positions.setdefault(subj_label, _shots.subject(scene, subj_label).root)
                key = subj_label
            else:
                key = "origin"
                positions.setdefault(key, Vec3(0.0, 0.0, 0.0))
            partner = spec.get("partnerLabel")
            if partner:
                positions.setdefault(partner, _shots.subject(scene, partner).root)
            elif st in _shots.PAIR_TYPES and subj_label:
                if figures is None:
                    figures = _shots.figure_positions(scene)
                partner = _shots.nearest({**figures, key: positions[key]}, key)
                if partner:
                    positions.setdefault(partner, figures[partner])
            end = frame + spec["durationFrames"] - 1
            board = Storyboard(description=spec.get("description") or None,
                               dialogue=spec.get("dialogue") or None,
                               beat=spec.get("action") or None, notes=spec.get("notes") or None)
            size = _shots.SHOT_TYPES.get(st, "two_shot" if st == "two-shot" else "ots")
            shot = _shots.size_shot(
                st, key, positions, partner=partner, focal_length=spec.get("focalLength"),
                distance=spec.get("distance"), azimuth=float(spec.get("angle") or 0.0),
                shot_id=sl.shot_name(
                    size, f"{subj_label}-{partner}" if st == "two-shot" and partner else subj_label,
                    over=partner if st == "over-shoulder" else None, index=i),
                frame_range=(frame, end), storyboard=board)
            built.append((shot, spec.get("cameraLabel") or f"{title}_Cam{i}", spec))
            frame = end + 1

        entries = []
        for n, (shot, cam_label, spec) in enumerate(built, start=1):
            created = False
            if save_presets:
                cam = _shots.find_camera(scene, cam_label)
                if cam is None:
                    cam = scene.create_camera(cam_label)
                    cam.label = cam_label  # a scripted camera's label is empty on Studio 4
                    created = True
                apply_shot(scene, shot, camera=cam, subjects=positions)
            position, aim = _shots.pose(shot, positions)
            start, end = shot.frame_range
            duration = end - start + 1
            entries.append({
                "shotNumber": n,
                "shotId": shot.id,
                "label": spec.get("label") or f"Shot {n}",
                "shotType": spec["shotType"],
                "subject": spec.get("subjectLabel"),
                "camera": cam_label,
                "cameraCreated": created,
                "applied": save_presets,
                "position": _shots.vec(position),
                "focalLength": shot.lens.focal_length,
                "distance": round(position.distance(aim), 1),
                "angle": spec.get("angle", 0),
                "startFrame": start,
                "endFrame": end,
                "durationFrames": duration,
                "durationSeconds": round(duration / 30, 1),
                "description": spec.get("description", ""),
                "action": spec.get("action", ""),
                "dialogue": spec.get("dialogue", ""),
            })
        total = frame - start_frame
        sequence = Sequence(id=sl.shot_name("storyboard", tag=title),
                            shots=tuple(s for s, _, _ in built),
                            storyboard=Storyboard(description=title))
        return {
            "title": title,
            "totalShots": len(entries),
            "totalFrames": total,
            "totalSeconds": round(total / 30, 1),
            "startFrame": start_frame,
            "endFrame": frame - 1,
            "shots": entries,
            "cameras": [e["camera"] for e in entries] if save_presets else [],
            "sequence": sequence.to_dict(),
            "suggestions": [
                "Use daz_set_active_camera to preview each shot's camera",
                "Use daz_render_with_camera to render individual shots",
                "Animate between shots with daz_animate_camera_movement",
                f"Set scene timeline: daz_set_frame_range({start_frame}, {frame - 1})",
            ],
        }

    return await _shots.run(_run)


# ---------------------------------------------------------------------------
# Phase 4.10: Focus & DOF tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_set_focus_point(
    camera_label: str,
    target_label: str | None = None,
    focal_distance: float | None = None,
    f_stop: float | None = None,
    enable_dof: bool = True,
) -> dict:
    """Set depth-of-field focus distance and aperture on a camera.

    Either focuses on a named scene node (distance measured from the camera)
    or sets an explicit focal distance in centimetres. Optionally enables DOF
    rendering and sets the F/Stop.

    Args:
        camera_label: Label of the camera node to configure (e.g. "Camera 1").
        target_label: Scene node to focus on: a figure's eyes, or another
            node's bounding-box centre. Takes precedence over focal_distance.
        focal_distance: Explicit focus distance in centimetres from the camera.
            Required if target_label is not provided.
        f_stop: Lens aperture (F/Stop value). Controls depth-of-field blur:
            - 1.4-2.8 -> very shallow DOF (cinematic portrait blur)
            - 4-5.6   -> moderate blur (standard portrait)
            - 8-11    -> deep DOF (landscape / group shots)
            If None, F/Stop is left unchanged.
        enable_dof: Whether to enable depth-of-field rendering on the camera
            (default True). Set False to only update distance without enabling DOF.

    Returns:
        dict with keys: camera, target, focalDistance, fStop, dofEnabled,
        propertiesSet, dofPreview (near/far limits of sharpness in cm from
        the thin-lens hyperfocal formula; far is null for infinity), suggestions.

    Examples:
        daz_set_focus_point("Camera 1", target_label="Genesis 9", f_stop=1.8)
        daz_set_focus_point("Camera 1", focal_distance=150, f_stop=4.0)

    Notes:
        - DOF effect is only visible in Iray/3Delight renders, not the viewport
        - Use daz_animate_focus_pull to animate a rack focus between subjects
    """
    if target_label is None and focal_distance is None:
        raise ToolError("Either target_label or focal_distance must be provided")
    if focal_distance is not None and focal_distance <= 0:
        raise ToolError("focal_distance must be greater than 0")
    if f_stop is not None and (f_stop < 0.7 or f_stop > 64):
        raise ToolError("f_stop must be between 0.7 and 64")

    def _run() -> dict[str, Any]:
        scene = get_scene()
        cam = _shots.camera(scene, camera_label)
        distance = focal_distance
        if target_label is not None:
            cam_pos = Vec3.from_dict(cam.position)
            point = _shots.subject(scene, target_label).focus_point
            distance = round(max(1.0, cam_pos.distance(point)), 1)
        props: dict[str, Any] = {}
        if enable_dof:
            cam.depth_of_field = True
            props["dofEnabled"] = True
        cam.focal_distance = distance
        props["focalDistance"] = distance
        if f_stop is not None:
            cam.f_stop = f_stop
            props["fStop"] = f_stop
        aperture = f_stop if f_stop is not None else cam.f_stop
        preview: dict[str, Any] = {"focalDistance": distance, "fStop": aperture,
                                   "nearSharp": None, "farSharp": None}
        if aperture:
            near, far = sl.depth_of_field_limits(cam.focal_length or 50.0, aperture, distance)
            preview.update(nearSharp=round(near, 1),
                           farSharp=None if far is None else round(far, 1))
        return {
            "camera": camera_label,
            "target": target_label,
            "focalDistance": distance,
            "fStop": f_stop,
            "dofEnabled": enable_dof,
            "propertiesSet": props,
            "dofPreview": preview,
            "suggestions": [
                "Use daz_animate_focus_pull to rack focus between subjects",
                "Lower F/Stop (e.g. 1.4) = shallower depth of field (more blur)",
                "Higher F/Stop (e.g. 11) = deeper depth of field (more in focus)",
                "Render with daz_render to see DOF effect",
            ],
        }

    return await _shots.run(_run)


@mcp.tool()
async def daz_animate_focus_pull(
    camera_label: str,
    from_target: str | None = None,
    to_target: str | None = None,
    from_distance: float | None = None,
    to_distance: float | None = None,
    start_frame: int = 0,
    end_frame: int = 60,
    hold_from_frames: int = 0,
    hold_to_frames: int = 0,
    f_stop: float | None = None,
) -> dict:
    """Animate a rack focus (focus pull) between two subjects or distances.

    Keys the camera's focal distance (``dazpy.shot_library.rack_focus``):
    hold sharp on subject A, pull to subject B, hold there. A figure is
    focused at its eyes, another node at its bounding-box centre, measured
    from the camera's current position. Existing focal-distance keys outside
    the pull are kept.

    Args:
        camera_label: Label of the camera node to animate (e.g. "Camera 1").
        from_target: Scene node label to focus at the start of the pull.
        to_target: Scene node label to focus at the end of the pull.
        from_distance: Explicit start focal distance in cm (when no from_target).
        to_distance: Explicit end focal distance in cm (when no to_target).
        start_frame: First frame of the animation range (default 0).
        end_frame: Last frame of the animation range (default 60 = 2 sec at 30fps).
        hold_from_frames: Frames to hold on the from-subject before pulling (default 0).
        hold_to_frames: Frames to hold on the to-subject after the pull (default 0).
            Holds that leave no time to pull are dropped.
        f_stop: Aperture to set. Low values (1.4-2.8) make the pull more visible.

    Returns:
        dict with keys: camera, fromTarget, fromDistance, toTarget, toDistance,
        fStop, focalDistanceProperty, startFrame, endFrame, pullStartFrame,
        pullEndFrame, keyframes[], pullDurationFrames, pullDurationSeconds
        (at 30 fps), suggestions.

    Examples:
        daz_animate_focus_pull("Camera 1", from_target="Alice", to_target="Bob",
                               start_frame=0, end_frame=119,
                               hold_from_frames=30, hold_to_frames=30, f_stop=1.8)

    Notes:
        - DOF is enabled on the camera automatically
        - Frame layout: [start] --hold-from-- [pull-start] -> [pull-end] --hold-to-- [end]
    """
    if from_target is None and from_distance is None:
        raise ToolError("Either from_target or from_distance must be provided")
    if to_target is None and to_distance is None:
        raise ToolError("Either to_target or to_distance must be provided")
    if start_frame < 0 or end_frame <= start_frame:
        raise ToolError("start_frame must be >= 0 and end_frame must be > start_frame")
    if hold_from_frames < 0 or hold_to_frames < 0:
        raise ToolError("hold_from_frames and hold_to_frames must be >= 0")
    if f_stop is not None and (f_stop < 0.7 or f_stop > 64):
        raise ToolError("f_stop must be between 0.7 and 64")
    for name, value in (("from_distance", from_distance), ("to_distance", to_distance)):
        if value is not None and value <= 0:
            raise ToolError(f"{name} must be greater than 0")
    pull_start, pull_end = start_frame + hold_from_frames, end_frame - hold_to_frames
    if pull_start >= pull_end:  # same rule as rack_focus: holds that leave no pull are dropped
        pull_start, pull_end = start_frame, end_frame

    def _run() -> dict[str, Any]:
        scene = get_scene()
        cam = _shots.camera(scene, camera_label)
        cam_pos = Vec3.from_dict(cam.position)
        frm = _shots.subject(scene, from_target).focus_point if from_target else from_distance
        to = _shots.subject(scene, to_target).focus_point if to_target else to_distance
        pull = sl.rack_focus(cam_pos, frm, to, start=start_frame, end=end_frame,
                             hold_from=hold_from_frames, hold_to=hold_to_frames)
        cam.depth_of_field = True
        for k in pull.keys:
            cam.set_focal_distance_at_frame(k.frame, k.focal_distance)
        if f_stop is not None:
            cam.f_stop = f_stop
        # Later entries win: without holds the start/end keys are the pull's own.
        phase = {start_frame: "hold-from", end_frame: "hold-to",
                 pull_start: "pull-start", pull_end: "pull-end"}
        return {
            "camera": camera_label,
            "fromTarget": from_target,
            "fromDistance": round(pull.keys[0].focal_distance, 1),
            "toTarget": to_target,
            "toDistance": round(pull.keys[-1].focal_distance, 1),
            "fStop": f_stop,
            "focalDistanceProperty": "Focal Distance",
            "startFrame": start_frame,
            "endFrame": end_frame,
            "pullStartFrame": pull_start,
            "pullEndFrame": pull_end,
            "keyframes": [{"frame": k.frame, "focalDistance": round(k.focal_distance, 1),
                           "phase": phase[k.frame]} for k in pull.keys],
            "pullDurationFrames": pull_end - pull_start,
            "pullDurationSeconds": round((pull_end - pull_start) / 30, 1),
            "suggestions": [
                "Render with daz_render_animation to see the focus pull in motion",
                "Adjust hold_from_frames / hold_to_frames to pause before and after the pull",
                "Combine with daz_animate_camera_movement for a dolly + focus pull",
                "Use F/Stop 1.4-2.8 for shallow DOF, 8-16 for deep DOF",
            ],
        }

    return await _shots.run(_run)


# ---------------------------------------------------------------------------
# Phase 4.11: Visual Composition tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_set_scene_atmosphere(
    environment_mode: int | None = None,
    environment_intensity: float | None = None,
    draw_dome: bool | None = None,
    dome_scale: float | None = None,
    dome_rotation: float | None = None,
    sun_light_intensity: float | None = None,
) -> dict:
    """Configure the DAZ Studio environment node for scene atmosphere and mood.

    Controls the Environment node (always `Scene.getNode(1)`) which governs the
    HDRI dome, Sun-Sky system, and ambient lighting. Call with only the parameters
    you want to change — others are left untouched.

    Args:
        environment_mode: Sets the overall lighting environment:
            - 0 = Dome and Scene (HDRI dome plus scene lights; Studio's default)
            - 1 = Dome Only      (HDRI dome image, scene lights ignored)
            - 2 = Sun-Sky Only   (procedural sun and sky)
            - 3 = Scene Only     (use only scene lights — disables dome/sun entirely)
            Mode 3 is required when using lighting presets or the daz_apply_visual_style
            tool so that scene lights are not washed out by ambient dome light.
        environment_intensity: Brightness of the HDRI dome/sun-sky (0.0–10.0).
            1.0 = default. Lower to 0.1–0.3 to blend HDRI with scene lights.
            Only has effect in modes 0, 1, 2.
        draw_dome: Whether the HDRI dome image is visible as the render background
            (True) or only contributes lighting (False).
        dome_scale: Scale of the dome geometry (default 1.0). Larger values push
            the horizon further away.
        dome_rotation: Horizontal rotation of the HDRI dome in degrees (0–360).
            Rotate to align HDRI sun direction with key lights.
        sun_light_intensity: Brightness of the Sun-Sky sun component (0.0–10.0).
            Only applies when environment_mode is 0 or 2.

    Returns:
        dict with keys: environmentNodeLabel, changesApplied (list of strings),
        changeCount, currentEnvironmentMode, results, environmentModeReference,
        suggestions.

    Examples:
        # Set to scene-lights-only mode (required before lighting presets)
        result = daz_set_scene_atmosphere(environment_mode=3)

        # HDRI dome at reduced intensity so scene lights dominate
        result = daz_set_scene_atmosphere(
            environment_mode=1,
            environment_intensity=0.2,
            draw_dome=True
        )

        # Rotate dome to match key light direction
        result = daz_set_scene_atmosphere(dome_rotation=135)

        # Outdoor scene with visible sky but dimmed ambient
        result = daz_set_scene_atmosphere(
            environment_mode=2,
            environment_intensity=0.4,
            sun_light_intensity=0.6,
            draw_dome=True
        )

    Notes:
        - The Environment node is always at Scene.getNode(1) in DAZ Studio
        - Property names vary across DAZ Studio versions; the tool tries multiple names
        - Mode 3 is automatically set by daz_apply_lighting_preset and daz_apply_visual_style
        - Changes are immediate but only visible in rendered output (not realtime viewport)
    """
    if environment_mode is not None and environment_mode not in _VALID_ENV_MODES:
        raise ToolError(
            f"Invalid environment_mode {environment_mode}. "
            "Valid: 0 (Dome and Scene), 1 (Dome Only), 2 (Sun-Sky Only), 3 (Scene Only)"
        )
    if environment_intensity is not None and not 0.0 <= environment_intensity <= 10.0:
        raise ToolError("environment_intensity must be between 0.0 and 10.0")
    if dome_scale is not None and not 0.01 <= dome_scale <= 100.0:
        raise ToolError("dome_scale must be between 0.01 and 100.0")
    if dome_rotation is not None and not 0.0 <= dome_rotation <= 360.0:
        raise ToolError("dome_rotation must be between 0.0 and 360.0")
    if sun_light_intensity is not None and not 0.0 <= sun_light_intensity <= 10.0:
        raise ToolError("sun_light_intensity must be between 0.0 and 10.0")

    result = await run_tool(lambda: _lighting.scene_atmosphere(
        environment_mode, environment_intensity, draw_dome, dome_scale, dome_rotation,
        sun_light_intensity))
    result["suggestions"] = [
        "Mode 3 (Scene Only) works best with daz_apply_lighting_preset presets",
        "Mode 1 (Dome Only) requires loading an HDRI map first",
        "Rotate dome to match light direction with key lights",
        "Lower environmentIntensity (0.1-0.5) to blend HDRI with scene lights",
    ]
    return result


@mcp.tool()
async def daz_apply_visual_style(
    style_name: str,
    subject_label: str | None = None,
    intensity: float = 1.0,
) -> dict:
    """Apply a holistic cinematic visual style to the scene's lighting and environment.

    Creates or reconfigures three named lights (Style_Key, Style_Fill, Style_Rim)
    with ratios, angles, and shadow softness tuned for the chosen style. Sets the
    environment to Scene Only mode so dome lighting does not interfere.

    Args:
        style_name: Named cinematic look — one of:
            - "cinematic"    High contrast, strong rim, compressed fill. Film look.
            - "noir"         Extreme contrast, deep shadows, minimal fill. Classic noir.
            - "golden-hour"  Warm raking key, blazing backlit rim. Magic hour.
            - "blue-hour"    Low intensity, even fill, cool tones. Dusk/dawn.
            - "high-key"     Bright, low contrast, minimal shadows. Commercial/fashion.
            - "low-key"      Dark, moody, shadows dominate. Thriller/horror.
            - "documentary"  Natural-feeling, moderate contrast. Interview/realistic.
            - "fantasy"      Ethereal, glowing rim, soft key. Magical/otherworldly.
        subject_label: Scene node to aim lights at and position lights around.
            If omitted, lights are positioned relative to scene origin.
        intensity: Scale factor for all light flux values (default 1.0).
            Use 0.5 for a subtler look, 2.0 for a punchier/brighter version.

    Returns:
        dict with keys: styleName, description, intensity, subject,
        environmentMode, lights (list of {role, label, flux, angle}),
        lightingRatios ({key, fill, rim, keyToFill, keyToRim}), suggestions.

    Examples:
        # Classic film look on Genesis 9
        result = daz_apply_visual_style("cinematic", subject_label="Genesis 9")

        # Darker noir at 80% intensity
        result = daz_apply_visual_style("noir", subject_label="Alice", intensity=0.8)

        # High-key commercial look, then fine-tune
        result = daz_apply_visual_style("high-key", subject_label="Product")
        daz_set_property("Style_Fill", "Flux", 6000)  # boost fill further

        # Fantasy glow style for group scene
        result = daz_apply_visual_style("fantasy", subject_label="Hero", intensity=1.2)

    Notes:
        - Creates lights named Style_Key, Style_Fill, Style_Rim (reuses if existing)
        - Sets environment to mode 3 (Scene Only) automatically
        - keyToFill ratio indicates contrast level: >6 = high contrast, <3 = low contrast
        - Lights use DAZ SpotLight nodes positioned 250 cm from subject
        - After applying, fine-tune individual lights with daz_set_property
        - Combine with daz_set_scene_atmosphere for additional environment control
        - For time-based mood changes use daz_animate_light on the Style_* lights
    """
    if style_name not in _VALID_VISUAL_STYLES:
        raise ToolError(
            f"Invalid style_name '{style_name}'. "
            f"Valid: {', '.join(sorted(_VALID_VISUAL_STYLES))}"
        )
    if not 0.1 <= intensity <= 5.0:
        raise ToolError("intensity must be between 0.1 and 5.0")

    result = await run_tool(lambda: _lighting.visual_style(style_name, subject_label, intensity))
    result["suggestions"] = [
        "Adjust intensity (0.5–2.0) to scale the whole look brighter or darker",
        "Fine-tune individual lights with daz_set_property on Style_Key/Fill/Rim",
        "Combine with daz_set_scene_atmosphere to control the environment dome",
        "Use daz_animate_light on Style_Key for dynamic lighting within the style",
    ]
    return result


# ---------------------------------------------------------------------------
# Phase 4.12: Multi-Scene Management tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_export_node_config(
    output_path: str,
    node_labels: list[str] | None = None,
    include_types: list[str] | None = None,
) -> dict:
    """Export scene node properties to a JSON file for reuse across scenes.

    Reads transforms, morphs, lights, and camera settings from the current scene
    and writes them to a JSON file on disk. The file can be loaded back into any
    scene with daz_import_node_config — even after a server restart or in a
    completely different DAZ Studio scene.

    This complements the in-memory daz_save_scene_state / daz_restore_scene_state
    system by providing persistent, portable, file-based storage.

    Args:
        output_path: Absolute path for the output JSON file (e.g.
            "C:/shots/hero_pose.json"). The file is created or overwritten.
        node_labels: List of node labels to capture. If omitted or empty, captures
            all skeletons, cameras, and lights in the scene.
        include_types: List of property categories to capture. Defaults to all:
            - "transforms": XTranslate/YTranslate/ZTranslate/XRotate/YRotate/ZRotate/Scale
            - "morphs": All non-zero numeric morph properties
            - "lights": Flux, Shadow Softness, Spread Angle, Photometric Mode
            - "cameras": FocalLength, Focal Distance, F/Stop, DOF properties

    Returns:
        dict with keys: outputPath, nodeCount, propertyCount, morphCount,
        nodeLabels (list of captured nodes), fileSizeBytes, suggestions.

    Examples:
        # Export entire scene setup (all figures, cameras, lights)
        result = daz_export_node_config("C:/projects/scene01_hero.json")

        # Export only characters (poses + morphs)
        result = daz_export_node_config(
            "C:/shots/pose_library/alice_surprised.json",
            node_labels=["Alice", "Bob"],
            include_types=["transforms", "morphs"]
        )

        # Export camera rig only
        result = daz_export_node_config(
            "C:/presets/interview_cameras.json",
            node_labels=["Camera A", "Camera B", "Camera C"],
            include_types=["transforms", "cameras"]
        )

        # Export lighting setup
        result = daz_export_node_config(
            "C:/presets/rembrandt_lights.json",
            include_types=["transforms", "lights"]
        )

    Notes:
        - Morphs are only captured if their value is non-zero (active morphs only)
        - Output file is human-readable JSON — you can inspect and hand-edit it
        - Use daz_import_node_config to restore in any scene
        - For in-session (non-persistent) checkpoints, use daz_save_scene_state
        - Node matching on import uses exact label matching
    """
    if not output_path:
        raise ToolError("output_path must not be empty")

    valid_include_types = {"transforms", "morphs", "lights", "cameras"}
    if include_types is None:
        include_types = list(valid_include_types)
    else:
        invalid = set(include_types) - valid_include_types
        if invalid:
            raise ToolError(
                f"Invalid include_types: {sorted(invalid)}. "
                f"Valid: {sorted(valid_include_types)}"
            )

    # Read from DAZ Studio
    result = await run_tool(lambda: _read_node_config(node_labels or [], include_types))

    # Write to disk (Python side handles file I/O)
    config_data = result.get("config", {})
    summary = result.get("summary", {})

    output_file = Path(output_path)
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "vangard_config_version": "1.0",
                "include_types": include_types,
                "node_count": summary.get("nodes", 0),
                "nodes": config_data,
            }, f, indent=2)
    except OSError as e:
        raise ToolError(f"Failed to write config file: {e}") from e

    file_size = output_file.stat().st_size

    return {
        "outputPath": str(output_file),
        "nodeCount": summary.get("nodes", 0),
        "propertyCount": summary.get("properties", 0),
        "morphCount": summary.get("morphs", 0),
        "nodeLabels": list(config_data.keys()),
        "fileSizeBytes": file_size,
        "suggestions": [
            "Use daz_import_node_config to restore this setup in any scene",
            "Edit the JSON file to adjust specific values before importing",
            "Keep pose files, lighting files, and camera files separate for modular reuse",
        ],
    }


@mcp.tool()
async def daz_import_node_config(
    input_path: str,
    node_labels: list[str] | None = None,
    skip_missing: bool = True,
    scale_transforms: float = 1.0,
) -> dict:
    """Apply a previously exported node configuration file to the current scene.

    Reads a JSON config file created by daz_export_node_config and applies the
    stored property values to matching nodes in the current scene. Nodes are
    matched by exact label. Missing nodes are skipped by default.

    Args:
        input_path: Absolute path to the JSON config file to import.
        node_labels: Subset of node labels to import from the file. If omitted,
            all nodes in the file are imported. Use this to import just Alice's
            pose from a file that contains multiple characters.
        skip_missing: If True (default), silently skip nodes in the file that
            don't exist in the current scene. If False, report them as errors.
        scale_transforms: Scale factor applied to XTranslate/YTranslate/ZTranslate
            values before applying (default 1.0 = no scaling). Use 0.01 to convert
            cm→m if the source scene used different units.

    Returns:
        dict with keys: inputPath, totalNodes, successCount, failureCount,
        skippedCount, results (per-node detail), suggestions.

    Examples:
        # Restore a full scene setup
        result = daz_import_node_config("C:/projects/scene01_hero.json")

        # Import only Alice's pose from a multi-character file
        result = daz_import_node_config(
            "C:/shots/pose_library/crowd_setup.json",
            node_labels=["Alice"]
        )

        # Apply a camera preset, ignoring if cameras don't exist
        result = daz_import_node_config(
            "C:/presets/interview_cameras.json",
            skip_missing=True
        )

        # Import lighting config from a different scene's export
        result = daz_import_node_config("C:/presets/rembrandt_lights.json")
        # Check which lights were found
        for r in result["results"]:
            print(r["node"], r["status"], r.get("applied", []))

    Notes:
        - Node matching is exact label matching — rename nodes in the scene if needed
        - Only properties that exist on the target node are set; others are skipped
        - Morph properties that don't exist on a different figure generation are silently skipped
        - Use scale_transforms=1.0 for scenes in the same unit system
        - For in-session restoration (faster), use daz_restore_scene_state instead
    """
    if not input_path:
        raise ToolError("input_path must not be empty")
    if not 0.0001 <= scale_transforms <= 1000.0:
        raise ToolError("scale_transforms must be between 0.0001 and 1000.0")

    input_file = Path(input_path)
    if not input_file.exists():
        raise ToolError(f"Config file not found: {input_path}")

    try:
        with open(input_file, encoding="utf-8") as f:
            file_data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ToolError(f"Failed to read config file: {e}") from e

    # Support both raw dict and the versioned wrapper written by export
    if "nodes" in file_data:
        config = file_data["nodes"]
    else:
        config = file_data

    # Filter to requested node labels
    if node_labels:
        config = {k: v for k, v in config.items() if k in node_labels}
        missing_labels = [lbl for lbl in node_labels if lbl not in config]
        if missing_labels:
            raise ToolError(
                f"These node labels were not found in the config file: {missing_labels}"
            )

    if not config:
        raise ToolError("No nodes to import (config is empty after filtering)")

    # Apply to DAZ Studio
    result = await run_tool(lambda: _write_node_config(config, skip_missing, scale_transforms))

    return {
        "inputPath": str(input_file),
        "totalNodes": result.get("totalNodes", 0),
        "successCount": result.get("successCount", 0),
        "failureCount": result.get("failureCount", 0),
        "skippedCount": result.get("skippedCount", 0),
        "results": result.get("results", []),
        "suggestions": [
            "Check 'skipped' nodes — they weren't found in the current scene",
            "Check 'partial' nodes — some properties didn't exist on the figure generation",
            "Use node_labels filter to import only specific characters from a multi-node file",
        ],
    }


# ---------------------------------------------------------------------------
# Phase 4.13: Performance Timing tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_time_expression(
    character_label: str,
    emotion: str,
    peak_frame: int,
    ease_in_frames: int = 10,
    hold_frames: int = 20,
    ease_out_frames: int = 15,
    intensity: float = 0.7,
    baseline_frame: int | None = None,
) -> dict:
    """Apply a timed emotional expression to a character using keyframed morphs.

    Unlike daz_set_emotion (which sets the current frame only), this tool creates
    a full keyframe arc: neutral → ease-in → peak hold → ease-out → neutral.
    The result is a performance beat — a moment of expression that rises, holds,
    and falls back over a specified number of frames.

    Args:
        character_label: Node label of the character to animate.
        emotion: Emotion name — one of:
            happy, sad, angry, surprised, fearful, disgusted, neutral,
            excited, bored, confident, shy, loving, contemptuous
        peak_frame: Frame number at which the expression reaches full intensity.
            The ease-in begins at (peak_frame - ease_in_frames).
        ease_in_frames: Frames to blend from neutral to peak (default 10).
            Set to 0 for an instant snap to the expression.
        hold_frames: Frames to hold the expression at peak before fading out
            (default 20). The expression stays at full intensity for this duration.
        ease_out_frames: Frames to return from peak to neutral (default 15).
            Set to 0 to hold the expression indefinitely (no return keyframe added).
        intensity: Peak expression intensity, 0.0–1.0 (default 0.7).
        baseline_frame: Optional frame before the ease-in to set a neutral (0)
            keyframe. Useful to prevent bleed from a previous expression.
            If None, no baseline keyframe is added.

    Returns:
        dict with keys: character, easeInStart, holdStart, holdEnd, easeOutEnd,
        intensity, appliedMorphs, bodyAdjustments, notFound, keyframesSet,
        durationFrames, holdFrames.

    Examples:
        # Alice looks surprised at frame 60, holds 20 frames, fades over 15
        result = daz_time_expression(
            "Alice", "surprised", peak_frame=60,
            ease_in_frames=8, hold_frames=20, ease_out_frames=15
        )
        # Keyframes: neutral@52 → peak@60 → peak@80 → neutral@95

        # Instant happy snap at frame 30 (no ease-in), 2-second hold at 30fps
        result = daz_time_expression(
            "Bob", "happy", peak_frame=30,
            ease_in_frames=0, hold_frames=60, ease_out_frames=20,
            intensity=0.9
        )

        # Sad expression with neutral baseline to clear previous state
        result = daz_time_expression(
            "Alice", "sad", peak_frame=120,
            ease_in_frames=20, hold_frames=40, ease_out_frames=30,
            baseline_frame=90
        )

        # Subtle confident look that doesn't fade (holds to end of scene)
        result = daz_time_expression(
            "Hero", "confident", peak_frame=45,
            ease_in_frames=15, hold_frames=200, ease_out_frames=0,
            intensity=0.5
        )

    Notes:
        - Uses the same morph candidate lists as daz_set_emotion; first match wins
        - notFound morphs are reported but do not raise errors
        - Frame layout: [baseline?] → [easeInStart=peak-ease_in] → [holdStart=peak]
                        → [holdEnd=peak+hold] → [easeOutEnd=holdEnd+ease_out]
        - ease_out_frames=0 means no ease-out keyframe — expression stays at peak
        - Combine multiple daz_time_expression calls on different characters for
          reaction sequences (see daz_sync_character_beats for automatic staggering)
    """
    if emotion not in _EMOTION_DEFINITIONS:
        valid = sorted(_EMOTION_DEFINITIONS.keys())
        raise ToolError(f"Unknown emotion '{emotion}'. Valid: {', '.join(valid)}")
    if not 0.0 <= intensity <= 1.0:
        raise ToolError("intensity must be between 0.0 and 1.0")
    if ease_in_frames < 0 or hold_frames < 0 or ease_out_frames < 0:
        raise ToolError("ease_in_frames, hold_frames, and ease_out_frames must be >= 0")
    if peak_frame < 0:
        raise ToolError("peak_frame must be >= 0")

    ease_in_start = max(0, peak_frame - ease_in_frames)
    hold_start    = peak_frame
    hold_end      = peak_frame + hold_frames
    ease_out_end  = hold_end + ease_out_frames

    if baseline_frame is not None and baseline_frame >= ease_in_start:
        raise ToolError(
            f"baseline_frame ({baseline_frame}) must be before ease_in_start ({ease_in_start})"
        )

    frames = (ease_in_start, hold_start, hold_end,
              ease_out_end if ease_out_frames > 0 else hold_end)
    return await run_tool(lambda: _time_expression(
        character_label, emotion, intensity, frames, baseline_frame))


@mcp.tool()
async def daz_sync_character_beats(
    beat_frame: int,
    characters: list[dict],
    stagger_frames: int = 5,
    ease_in_frames: int = 8,
    hold_frames: int = 20,
    ease_out_frames: int = 12,
) -> dict:
    """Synchronize timed expressions across multiple characters at a dramatic beat.

    Applies daz_time_expression to each character in sequence, staggering their
    peak frames slightly so reactions feel natural rather than robotically simultaneous.
    The first character peaks at beat_frame; subsequent characters peak at
    beat_frame + (index * stagger_frames).

    Args:
        beat_frame: Frame at which the primary (first) character peaks.
        characters: List of character definition dicts. Each dict must contain:
            - "label" (str): Scene node label of the character.
            - "emotion" (str): Emotion name (same set as daz_time_expression).
            Optional per-character overrides:
            - "intensity" (float): Override intensity for this character (default 0.7).
            - "stagger_offset" (int): Override frame offset from beat_frame for
              this character. Overrides automatic stagger_frames calculation.
            - "ease_in_frames" (int): Override ease-in duration.
            - "hold_frames" (int): Override hold duration.
            - "ease_out_frames" (int): Override ease-out duration.
        stagger_frames: Default frames between each character's peak
            (default 5). Set to 0 for simultaneous reactions.
        ease_in_frames: Default ease-in duration shared across all characters
            unless overridden per-character (default 8).
        hold_frames: Default hold duration (default 20).
        ease_out_frames: Default ease-out duration (default 12).

    Returns:
        dict with keys: beatFrame, characterCount, totalKeyframes,
        results (list of per-character daz_time_expression results),
        schedule (list of {character, emotion, peakFrame} for overview),
        suggestions.

    Examples:
        # Two characters react to shocking news — Alice first, Bob 5 frames later
        result = daz_sync_character_beats(
            beat_frame=90,
            characters=[
                {"label": "Alice", "emotion": "surprised"},
                {"label": "Bob",   "emotion": "fearful", "intensity": 0.6},
            ]
        )
        # Alice peaks at 90, Bob peaks at 95

        # Four-character group reaction with custom stagger
        result = daz_sync_character_beats(
            beat_frame=60,
            characters=[
                {"label": "Hero",    "emotion": "confident", "intensity": 0.9},
                {"label": "Villain", "emotion": "angry",     "intensity": 0.8},
                {"label": "Ally",    "emotion": "fearful"},
                {"label": "Bystander", "emotion": "surprised", "intensity": 0.4},
            ],
            stagger_frames=3,
            hold_frames=30
        )
        # Hero@60, Villain@63, Ally@66, Bystander@69

        # Simultaneous reaction (no stagger) — all peak at same frame
        result = daz_sync_character_beats(
            beat_frame=45,
            characters=[
                {"label": "A", "emotion": "happy"},
                {"label": "B", "emotion": "happy"},
            ],
            stagger_frames=0
        )

        # Mix of automatic and manual offsets
        result = daz_sync_character_beats(
            beat_frame=120,
            characters=[
                {"label": "Lead",    "emotion": "angry"},
                {"label": "Support", "emotion": "sad", "stagger_offset": 15},
            ]
        )
        # Lead@120, Support@135 (manual offset overrides stagger_frames)

    Notes:
        - Each character is processed sequentially; the full batch may take a
          few seconds for scenes with many morphs
        - Per-character errors do not abort the batch — check results for notFound
        - Combine with daz_animate_conversation for expression-timed dialogue scenes
        - Use baseline_frame in daz_time_expression to clear previous expressions
          before a beat (daz_sync_character_beats does not set baselines)
    """
    if not characters:
        return {"beatFrame": beat_frame, "characterCount": 0, "totalKeyframes": 0,
                "results": [], "schedule": [], "suggestions": []}
    if len(characters) > 10:
        raise ToolError("Maximum 10 characters per sync beat")
    if beat_frame < 0:
        raise ToolError("beat_frame must be >= 0")
    if stagger_frames < 0:
        raise ToolError("stagger_frames must be >= 0")

    # Validate all characters up front
    valid_emotions = sorted(_EMOTION_DEFINITIONS.keys())
    for i, char in enumerate(characters):
        if "label" not in char:
            raise ToolError(f"Character {i + 1} is missing required 'label' key")
        emotion = char.get("emotion", "neutral")
        if emotion not in _EMOTION_DEFINITIONS:
            raise ToolError(
                f"Character '{char['label']}' has unknown emotion '{emotion}'. "
                f"Valid: {', '.join(valid_emotions)}"
            )

    results = []
    schedule = []
    total_keyframes = 0

    for idx, char in enumerate(characters):
        label   = char["label"]
        emotion = char.get("emotion", "neutral")

        # Resolve peak frame: explicit offset takes priority, then auto-stagger
        if "stagger_offset" in char:
            peak_frame = beat_frame + int(char["stagger_offset"])
        else:
            peak_frame = beat_frame + idx * stagger_frames

        char_intensity = float(char.get("intensity", 0.7))
        char_ease_in   = int(char.get("ease_in_frames", ease_in_frames))
        char_hold      = int(char.get("hold_frames", hold_frames))
        char_ease_out  = int(char.get("ease_out_frames", ease_out_frames))

        ease_in_start = max(0, peak_frame - char_ease_in)
        hold_start    = peak_frame
        hold_end      = peak_frame + char_hold
        ease_out_end  = hold_end + char_ease_out

        frames = (ease_in_start, hold_start, hold_end,
                  ease_out_end if char_ease_out > 0 else hold_end)
        try:
            char_result = await run_tool(lambda label=label, emotion=emotion,  # noqa: E731
                                         intensity=char_intensity, frames=frames:
                                         _time_expression(label, emotion, intensity, frames,
                                                          None))
            total_keyframes += char_result.get("keyframesSet", 0)
            results.append({"character": label, "status": "ok", "detail": char_result})
        except Exception as e:
            results.append({"character": label, "status": "error", "error": str(e)})

        schedule.append({
            "character": label,
            "emotion": emotion,
            "intensity": char_intensity,
            "peakFrame": peak_frame,
            "easeInStart": ease_in_start,
            "easeOutEnd": ease_out_end if char_ease_out > 0 else hold_end,
        })

    success_count = sum(1 for r in results if r["status"] == "ok")
    return {
        "beatFrame": beat_frame,
        "characterCount": len(characters),
        "totalKeyframes": total_keyframes,
        "results": results,
        "schedule": schedule,
        "suggestions": [
            f"{success_count}/{len(characters)} characters processed successfully",
            "Check 'notFound' in each result for missing morphs on the figure generation",
            "Use daz_animate_conversation for camera + emotion sync in dialogue scenes",
            "Call daz_set_frame_range to extend timeline to cover all beat frames",
        ],
    }


# --- node config (export/import) on dazpy ----------------------------------

_CFG_TRANSFORMS = ("XTranslate", "YTranslate", "ZTranslate", "XRotate", "YRotate", "ZRotate",
                   "XScale", "YScale", "ZScale", "Scale")
_CFG_LIGHT = ("Flux", "Shadow Softness", "Spread Angle", "Photometric Mode")
_CFG_CAMERA = ("FocalLength", "Focal Distance", "Focus Distance", "F/Stop", "Depth of Field",
               "DOF Active")


def _skeleton_nodes(scene: Any) -> list:
    return scene.skeletons()


def _read_node_config(node_labels: list[str], include_types: list[str]) -> dict:
    """Capture name-keyed numeric properties per node (one call per node)."""
    scene = get_scene()
    if node_labels:
        nodes = []
        for label in node_labels:
            try:
                nodes.append(scene.resolve_node(label))
            except NodeNotFoundError:
                continue
    else:
        nodes = list(_skeleton_nodes(scene))
        nodes += [scene.resolve_node(str(c.element_id)) for c in scene.camera_info()]
        nodes += [scene.resolve_node(str(li.element_id)) for li in scene.light_info()]
    wanted = set()
    if "transforms" in include_types:
        wanted |= set(_CFG_TRANSFORMS)
    if "lights" in include_types:
        wanted |= set(_CFG_LIGHT)
    if "cameras" in include_types:
        wanted |= set(_CFG_CAMERA)
    config: dict[str, dict] = {}
    summary = {"nodes": 0, "properties": 0, "morphs": 0}
    for node in nodes:
        info = node.describe()
        data: dict[str, Any] = {"_type": info.type}
        others = {}
        for d in node.property_details("numeric"):
            if d.name in wanted:
                data[d.name] = d.value
            elif d.name not in _CFG_TRANSFORMS + _CFG_LIGHT + _CFG_CAMERA and d.value:
                others[d.name] = d.value
        if "morphs" in include_types:
            data.update(others)
            summary["morphs"] += len(others)
        config[info.label] = data
        summary["nodes"] += 1
        summary["properties"] += len(data) - 1
    return {"config": config, "summary": summary}


def _write_node_config(config: dict, skip_missing: bool, scale: float) -> dict:
    """Apply a node config in one dazpy batch; per-node ok/partial/skipped/error."""
    ops, owners = [], []
    for label, data in config.items():
        for name, value in data.items():
            if name == "_type":
                continue
            if scale != 1.0 and name in ("XTranslate", "YTranslate", "ZTranslate"):
                value = value * scale
            ops.append((label, name, value))
            owners.append(label)
    results = get_scene().set_numeric_properties(ops) if ops else []
    per_node: dict[str, dict] = {label: {"node": label, "applied": [], "failed": [],
                                         "missing": False} for label in config}
    for (label, name, _value), r in zip(ops, results):
        entry = per_node[label]
        if r.ok:
            entry["applied"].append(name)
        elif (r.error or "").startswith("Node not found"):
            entry["missing"] = True
        else:
            entry["failed"].append({"property": name, "error": r.error})
    return _summarize_node_writes(per_node, skip_missing)


def _summarize_node_writes(per_node: dict[str, dict], skip_missing: bool) -> dict:
    out, counts = [], {"ok": 0, "bad": 0, "skipped": 0}
    for label, e in per_node.items():
        if e["missing"]:
            key = "skipped" if skip_missing else "bad"
            counts[key] += 1
            out.append({"node": label, "status": "skipped" if skip_missing else "error",
                        "reason": "not found in scene"})
            continue
        status = "ok" if not e["failed"] else ("partial" if e["applied"] else "error")
        counts["bad" if status == "error" else "ok"] += 1
        out.append({"node": label, "status": status, "applied": e["applied"],
                    "failed": e["failed"]})
    return {"results": out, "successCount": counts["ok"], "failureCount": counts["bad"],
            "skippedCount": counts["skipped"], "totalNodes": len(per_node)}


# --- timed expressions on dazpy frame-based keys -----------------------------

def _expression_keys(peak: float, frames: tuple[int, int, int, int],
                     baseline: int | None) -> list[tuple[int, float]]:
    """0 -> peak -> hold -> 0 keys; a later key at the same frame wins."""
    ease_in, hold_start, hold_end, ease_out = frames
    keys: dict[int, float] = {}
    if baseline is not None and baseline < ease_in:
        keys[baseline] = 0.0
    keys[ease_in] = 0.0
    keys[max(ease_in, hold_start)] = peak
    if hold_end > hold_start:
        keys[hold_end] = peak
    if ease_out > hold_end:
        keys[ease_out] = 0.0
    return sorted(keys.items())


def _key_expression_face(skel: Any, definition: dict, intensity: float,
                         frames: tuple[int, int, int, int],
                         baseline: int | None) -> tuple[list, list, int]:
    """Key the full-face controller, else the feature dials. Returns
    (applied, not_found, keys written)."""
    face = definition.get("face", [])
    if face:
        keys = _expression_keys(intensity, frames, baseline)
        r = skel.key_numeric_candidates([(face, keys)])[0]
        if r.found:
            return [{"morph": r.matched, "peakValue": intensity}], [], len(keys)
    applied, not_found, keyed = [], [], 0
    slots = [(m["names"], m["value"] * intensity) for m in definition["morphs"]]
    if not slots:
        return applied, not_found, keyed
    keyed_slots = [(names, _expression_keys(peak, frames, baseline)) for names, peak in slots]
    for (names, peak), r in zip(slots, skel.key_numeric_candidates(keyed_slots)):
        if r.found:
            applied.append({"morph": r.matched, "peakValue": peak})
            keyed += len(_expression_keys(peak, frames, baseline))
        else:
            not_found.append(names[0] if names else "unknown")
    return applied, not_found, keyed


def _key_expression_body(skel: Any, adjustments: list[dict], intensity: float,
                         frames: tuple[int, int, int, int],
                         baseline: int | None) -> tuple[list, list, int]:
    """Key body bones (roles resolved per generation). Returns
    (applied, missing roles, keys written)."""
    bones = set(skel.bone_names())
    body, missing, data = [], [], {}
    for adj in adjustments:
        bone = resolve_bone(adj["bone"], bones)
        if bone is None:
            missing.append(adj["bone"])
            continue
        peak = adj["value"] * intensity
        data.setdefault(bone, {})[AXIS_BY_PROPERTY[adj["property"]]] = _expression_keys(
            peak, frames, baseline)
        body.append({"bone": bone, "property": adj["property"], "peakValue": peak})
    if data:
        skel.key_bone_axes(data)
    return body, missing, sum(len(k) for axes in data.values() for k in axes.values())


def _time_expression(label: str, emotion: str, intensity: float,
                     frames: tuple[int, int, int, int], baseline: int | None) -> dict:
    """Key *emotion* on *label*: the stock full-face controller when the figure
    has one (else the feature dials), plus body bones resolved per generation.
    Frames are timeline frames (the old script used them as DzTime ticks)."""
    skel = get_scene().resolve_node(label)
    definition = _EMOTION_DEFINITIONS[emotion]
    applied, not_found, face_keys = _key_expression_face(skel, definition, intensity, frames,
                                                         baseline)
    body, body_missing, body_keys = _key_expression_body(skel, definition["body"], intensity,
                                                         frames, baseline)
    return {"character": skel.describe().label, "easeInStart": frames[0],
            "holdStart": frames[1], "holdEnd": frames[2], "easeOutEnd": frames[3],
            "intensity": intensity, "appliedMorphs": applied, "bodyAdjustments": body,
            "notFound": not_found, "bodyNotFound": body_missing,
            "keyframesSet": face_keys + body_keys,
            "durationFrames": frames[3] - frames[0], "holdFrames": frames[2] - frames[1]}
