from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastmcp.exceptions import ToolError

from .._mcp import mcp, _execute_by_id


# ---------------------------------------------------------------------------
# Emotion definitions (shared with daz_time_expression / daz_sync_character_beats)
# ---------------------------------------------------------------------------

_EMOTION_DEFINITIONS: dict[str, dict] = {
    "happy": {
        "morphs": [
            {"names": ["PHMSmile", "Smile", "CTRLSmile", "MouthSmile", "SmileSimple"], "value": 0.85},
            {"names": ["PHMEyesSquint", "EyesSquint", "EyeSquintL", "SquintEyes"], "value": 0.25},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": 3.0}],
    },
    "sad": {
        "morphs": [
            {"names": ["PHMFrown", "Frown", "MouthFrown", "CTRLFrown", "FrownSimple"], "value": 0.75},
            {"names": ["PHMBrowInnerDown", "BrowDownL", "BrowDown", "CTRLBrowDown", "BrowInnerDown"], "value": 0.6},
            {"names": ["PHMEyesSquint", "EyesSquint", "EyeSquintL"], "value": 0.3},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": -6.0}],
    },
    "angry": {
        "morphs": [
            {"names": ["PHMFrown", "Frown", "MouthFrown", "CTRLFrown"], "value": 0.5},
            {"names": ["PHMBrowDown", "BrowDown", "BrowDownLeft", "CTRLBrowDown", "BrowDownR"], "value": 0.85},
            {"names": ["PHMNoseWrinkle", "NoseWrinkle", "NoseSneerL", "NoseSneer"], "value": 0.4},
            {"names": ["PHMEyesTighten", "EyesTighten", "EyeSquintL", "CheekSquintL"], "value": 0.4},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": -3.0}],
    },
    "surprised": {
        "morphs": [
            {"names": ["PHMBrowUp", "BrowUp", "BrowInnerUpL", "CTRLBrowUp", "BrowsUp"], "value": 0.85},
            {"names": ["PHMEyesWide", "EyesWide", "EyeOpenL", "EyeWideL"], "value": 0.75},
            {"names": ["PHMMouthOpen", "MouthOpen", "CTRLMouthOpen", "JawOpen"], "value": 0.6},
        ],
        "body": [],
    },
    "fearful": {
        "morphs": [
            {"names": ["PHMBrowUp", "BrowUp", "BrowInnerUpL", "CTRLBrowUp"], "value": 0.7},
            {"names": ["PHMEyesWide", "EyesWide", "EyeOpenL", "EyeWideL"], "value": 0.6},
            {"names": ["PHMMouthOpen", "MouthOpen", "CTRLMouthOpen", "JawOpen"], "value": 0.3},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": -4.0}],
    },
    "disgusted": {
        "morphs": [
            {"names": ["PHMNoseWrinkle", "NoseWrinkle", "NoseSneerL", "NoseSneer"], "value": 0.75},
            {"names": ["PHMFrown", "Frown", "MouthFrown", "CTRLFrown"], "value": 0.4},
            {"names": ["PHMUpperLipUp", "UpperLipUp", "MouthUpperUp_L", "LipUpperUp_L"], "value": 0.3},
        ],
        "body": [],
    },
    "neutral": {
        "morphs": [],
        "body": [],
    },
    "excited": {
        "morphs": [
            {"names": ["PHMSmile", "Smile", "CTRLSmile", "MouthSmile"], "value": 1.0},
            {"names": ["PHMBrowUp", "BrowUp", "CTRLBrowUp", "BrowsUp"], "value": 0.5},
            {"names": ["PHMEyesWide", "EyesWide", "EyeOpenL"], "value": 0.4},
            {"names": ["PHMMouthOpen", "MouthOpen", "CTRLMouthOpen", "JawOpen"], "value": 0.4},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": 5.0}],
    },
    "bored": {
        "morphs": [
            {"names": ["PHMEyesClosed", "EyesClosed", "EyeClosedL", "CTRLEyesClosed"], "value": 0.4},
            {"names": ["PHMFrown", "Frown", "MouthFrown"], "value": 0.2},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": -4.0}],
    },
    "confident": {
        "morphs": [
            {"names": ["PHMSmile", "Smile", "MouthSmile", "CTRLSmile"], "value": 0.3},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": 4.0}],
    },
    "shy": {
        "morphs": [
            {"names": ["PHMSmile", "Smile", "MouthSmile"], "value": 0.2},
            {"names": ["PHMEyesSquint", "EyesSquint", "EyeSquintL"], "value": 0.15},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": -5.0}],
    },
    "loving": {
        "morphs": [
            {"names": ["PHMSmile", "Smile", "MouthSmile", "CTRLSmile"], "value": 0.6},
            {"names": ["PHMEyesSquint", "EyesSquint", "EyeSquintL"], "value": 0.35},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": 2.0}],
    },
    "contemptuous": {
        "morphs": [
            {"names": ["PHMSmileR", "SmileR", "MouthSmileR", "MouthSmile_R"], "value": 0.5},
            {"names": ["PHMFrownL", "FrownL", "MouthFrownL", "MouthFrown_L"], "value": 0.3},
        ],
        "body": [],
    },
}

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
) -> dict[str, Any]:
    """Create a multi-camera shot sequence for cinematic storytelling.

    Automatically creates and positions multiple cameras with keyframe animations
    for standard cinematic sequences. Useful for:
    - Conversations (shot-reverse-shot)
    - Establishing shots (wide → medium → close-up)
    - Product showcases (orbit)
    - Dramatic reveals (push-in)

    Args:
        sequence_type: Type of sequence to create. Options:
            - "establishing-medium-closeup": Three cameras at different distances
              (wide → medium → close-up). Frames divided equally into thirds.
            - "shot-reverse-shot": Two cameras for conversation, alternating between
              over-shoulder angles. Requires 2 characters. Frames split 50/50.
            - "orbit": Single camera orbiting 360° around subject with keyframe animation.
            - "push-in": Single camera dollying from wide shot to close-up with smooth animation.

        characters: List of character labels (1-2 depending on sequence).
            First character is primary subject. Second character used for shot-reverse-shot.

        duration: Total duration in frames (default: 120 frames = 4 seconds at 30fps).

    Returns:
        Dict with:
        - cameras: List of created cameras with position and frame range info
        - totalFrames: Total duration
        - sequenceType: Confirmed sequence type
        - subject: Primary subject character label

    Example:
        # Establishing sequence for single character
        daz_create_shot_sequence(
            "establishing-medium-closeup",
            ["Genesis 9"],
            duration=180
        )
        # Creates: Wide Shot (0-59), Medium Shot (60-119), Close-up Shot (120-179)

        # Conversation between two characters
        daz_create_shot_sequence(
            "shot-reverse-shot",
            ["Alice", "Bob"],
            duration=240
        )
        # Creates: Over Shoulder 1 (0-119), Over Shoulder 2 (120-239)

        # 360° orbit around character
        daz_create_shot_sequence(
            "orbit",
            ["Genesis 9"],
            duration=300
        )
        # Creates animated camera orbiting over 300 frames

        # Dolly push-in
        daz_create_shot_sequence(
            "push-in",
            ["Genesis 9"],
            duration=120
        )
        # Creates animated camera moving from wide to close-up

    Notes:
        - Cameras are automatically aimed at subject's eye level
        - For animated sequences (orbit, push-in), keyframes are set automatically
        - For multi-shot sequences (establishing, shot-reverse-shot), use frame ranges
          to determine which camera to render for each frame
        - Use daz_set_active_camera() to preview each camera angle
        - Use daz_set_frame() to scrub through animation timeline
    """
    # Validate sequence type
    valid_types = [
        "establishing-medium-closeup",
        "shot-reverse-shot",
        "orbit",
        "push-in",
    ]
    if sequence_type not in valid_types:
        raise ToolError(
            f"Invalid sequence_type '{sequence_type}'. "
            f"Valid options: {', '.join(valid_types)}"
        )

    # Characters are optional — cameras aim at scene origin when none provided

    if sequence_type == "shot-reverse-shot" and len(characters) < 2:
        raise ToolError("shot-reverse-shot requires 2 characters")

    # Validate duration
    if duration < 10 or duration > 10000:
        raise ToolError("Duration must be between 10 and 10000 frames")

    return await _execute_by_id("vangard-create-shot-sequence", {
        "sequenceType": sequence_type,
        "characters": characters,
        "duration": duration,
        "fps": 30,
    })


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
        - sceneType: Detected scene type ("dining", "interview", "portrait", "conversation", "generic")
        - description: Original description
        - charactersUsed: Number of characters processed
        - actions: List of actions performed (what was set up)
        - cameras: List of created cameras with type and purpose
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

        3. **Cameras**: Multiple camera angles appropriate for scene
           - Wide shots for establishing
           - Medium shots for general coverage
           - Close-ups for portraits
           - Over-shoulder for conversations

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

    return await _execute_by_id("vangard-create-scene", {
        "description": description,
        "characters": chars,
    })


# ---------------------------------------------------------------------------
# Camera Movement & Animation Tools (Phase 4.5)
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_animate_camera_movement(
    camera_label: str,
    movement_type: str,
    start_frame: int = 0,
    end_frame: int = 120,
    intensity: float = 1.0,
) -> dict[str, Any]:
    """Animate common camera movements with keyframes.

    Creates keyframe animation for standard cinematic camera moves. Perfect for
    adding professional camera motion without manual keyframing.

    Args:
        camera_label: Label of camera to animate
        movement_type: Type of camera movement. Options:
            - "dolly-in": Move camera forward toward aim point
            - "dolly-out": Move camera backward away from aim point
            - "pan-left": Rotate camera left (horizontal)
            - "pan-right": Rotate camera right (horizontal)
            - "tilt-up": Rotate camera up (vertical)
            - "tilt-down": Rotate camera down (vertical)
            - "crane-up": Move camera vertically upward
            - "crane-down": Move camera vertically downward
            - "handheld-shake": Procedural shake animation
        start_frame: Animation start frame (default: 0)
        end_frame: Animation end frame (default: 120)
        intensity: Movement amount multiplier 0.0-2.0 (default: 1.0)
            - dolly/crane: Distance in cm (200cm * intensity)
            - pan/tilt: Rotation in degrees (45° * intensity for pan, 30° for tilt)
            - shake: Amplitude (5cm * intensity)

    Returns:
        Dict with:
        - camera: Camera label
        - movementType: Type of movement applied
        - keyframesSet: Number of keyframes created
        - frameRange: {start, end} frame range
        - description: Human-readable description of movement
        - intensity: Applied intensity value

    Example:
        # Slow dolly-in
        daz_animate_camera_movement("Camera 1", "dolly-in", 0, 180, intensity=1.0)

        # Quick pan right
        daz_animate_camera_movement("Camera 1", "pan-right", 0, 60, intensity=1.5)

        # Subtle handheld shake
        daz_animate_camera_movement("Camera 1", "handheld-shake", 0, 300, intensity=0.3)

        # Dramatic crane up
        daz_animate_camera_movement("Camera 1", "crane-up", 60, 150, intensity=2.0)

    Notes:
        - Creates smooth motion by default
        - Dolly moves camera along current aim direction
        - Pan/tilt preserve camera position
        - Crane moves only vertically
        - Shake creates randomized keyframes every 3 frames
        - All movements create proper keyframe animations
        - Intensity scales movement amount (useful for subtle vs dramatic moves)
        - Handheld shake uses random offsets for natural camera shake
    """
    # Validate camera label
    if not camera_label:
        raise ToolError("camera_label is required")

    # Validate movement type
    valid_movements = [
        "dolly-in", "dolly-out",
        "pan-left", "pan-right",
        "tilt-up", "tilt-down",
        "crane-up", "crane-down",
        "handheld-shake"
    ]
    if movement_type not in valid_movements:
        raise ToolError(
            f"Invalid movement_type '{movement_type}'. "
            f"Valid options: {', '.join(valid_movements)}"
        )

    # Validate frame range
    if start_frame < 0:
        raise ToolError("start_frame must be >= 0")
    if end_frame <= start_frame:
        raise ToolError(f"end_frame ({end_frame}) must be > start_frame ({start_frame})")
    if end_frame - start_frame > 10000:
        raise ToolError("Frame range too large (max 10000 frames)")

    # Validate intensity
    if intensity < 0 or intensity > 10:
        raise ToolError("intensity must be between 0 and 10")

    return await _execute_by_id("vangard-animate-camera-movement", {
        "cameraLabel": camera_label,
        "movementType": movement_type,
        "startFrame": start_frame,
        "endFrame": end_frame,
        "intensity": intensity,
    })


@mcp.tool()
async def daz_create_camera_path(
    camera_label: str,
    waypoints: list[dict[str, Any]],
    easing: str = "smooth",
    aim_at_target: str | None = None,
) -> dict[str, Any]:
    """Create smooth camera path through multiple waypoints.

    Creates a smooth animated camera path by interpolating between position waypoints.
    Perfect for tracking shots, reveals, and complex camera moves.

    Args:
        camera_label: Label of camera to animate
        waypoints: List of waypoint dicts, each containing:
            - position: Dict with x, y, z coordinates (world space, cm)
            - frame: Frame number for this waypoint
            Minimum 2 waypoints required. Automatically sorted by frame.
        easing: Interpolation type (default: "smooth")
            - "linear": Constant speed between waypoints
            - "smooth": Ease-in-out (slow start/end, fast middle)
            - "ease-in": Slow start, fast end
            - "ease-out": Fast start, slow end
        aim_at_target: Optional node label to track throughout movement

    Returns:
        Dict with:
        - camera: Camera label
        - waypointCount: Number of waypoints
        - easing: Easing type used
        - keyframesSet: Number of keyframes created
        - frameRange: {start, end} frame range
        - aimAtTarget: Target node label if specified

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
        - Waypoints are automatically sorted by frame
        - Creates 3 keyframes per waypoint (X, Y, Z translate)
        - Easing currently applied at DazScript keyframe level
        - aim_at_target points camera at target throughout path
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

    return await _execute_by_id("vangard-create-camera-path", {
        "cameraLabel": camera_label,
        "waypoints": waypoints,
        "easing": easing,
        "aimAtTarget": aim_at_target,
    })


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
                "suggestions": ["Add a second character to the scene to choreograph a " + action_type]}

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
    camera_height: float = 160.0,
    auto_aim: bool = True,
) -> dict[str, Any]:
    """Create multiple camera angles for cinematic coverage of a subject.

    Automatically positions multiple cameras for professional shot coverage (master,
    medium, closeup, etc.) based on cinematic conventions. All cameras aim at the
    subject and use appropriate focal lengths for each shot type.

    Args:
        subject_label: Label of subject node (character, prop, etc.)
        coverage_type: Type of coverage to set up:
            - "standard": Master (wide), Medium, Closeup (3 cameras)
            - "interview": Two-shot + two singles at angles (3 cameras)
            - "dramatic": Master, Low Angle, High Angle, Profile (4 cameras)
            - "action": Wide, Medium, Tracking, Hero Low (4 cameras)
        camera_height: Height of cameras in cm (default: 160 = eye level)
        auto_aim: Automatically point cameras at subject (default: True)

    Returns:
        Dict with:
        - coverageType: Type of coverage used
        - subject: Subject label
        - subjectPosition: {x, y, z} position of subject
        - cameras: List of dicts with name, label, position, focalLength, distance, angle
        - cameraCount: Number of cameras created
        - suggestions: List of recommended next steps

    Example:
        # Standard 3-camera coverage for dialogue scene
        result = daz_setup_shot_coverage(
            "Alice",
            coverage_type="standard",
            camera_height=165,
            auto_aim=True
        )
        # Creates Master (35mm, 400cm), Medium (50mm, 200cm), Closeup (85mm, 100cm)

        # Interview setup with two-shot + singles
        result = daz_setup_shot_coverage(
            "Interviewer",
            coverage_type="interview",
            camera_height=160
        )
        # Creates TwoShot (50mm), SingleA (85mm, -30°), SingleB (85mm, +30°)

        # Dramatic multi-angle coverage
        result = daz_setup_shot_coverage(
            "Hero",
            coverage_type="dramatic",
            camera_height=170
        )
        # Creates Master, LowAngle (-80cm), HighAngle (+120cm), Profile (90°)

        # Action scene with dynamic angles
        result = daz_setup_shot_coverage(
            "Stunt_Character",
            coverage_type="action",
            camera_height=150
        )
        # Creates WideAction (28mm), MediumAction, TrackingShot (-45°), HeroLow

    Notes:
        - All cameras automatically created and positioned
        - Focal lengths chosen for each shot type (28-85mm range)
        - Standard coverage: 3 cameras (most common setup)
        - Interview: 3 cameras (two-shot + singles)
        - Dramatic: 4 cameras (varied angles and heights)
        - Action: 4 cameras (wide coverage + low angles)
        - Cameras named by shot type (Master_Camera, Closeup_Camera, etc.)
        - Switch active camera to render different angles
        - Use with daz_animate_camera_movement for dynamic shots
        - Combine with daz_render_animation to output multiple angles
    """
    # Validate coverage type
    valid_types = ["standard", "interview", "dramatic", "action"]
    if coverage_type not in valid_types:
        raise ToolError(
            f"Invalid coverage_type '{coverage_type}'. "
            f"Valid options: {', '.join(valid_types)}"
        )

    # Validate camera height
    if camera_height < 0 or camera_height > 500:
        raise ToolError("camera_height must be between 0 and 500 cm")

    return await _execute_by_id("vangard-setup-shot-coverage", {
        "subjectLabel": subject_label,
        "coverageType": coverage_type,
        "cameraHeight": camera_height,
        "autoAim": auto_aim,
    })


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

    Creates multiple cameras arranged in a circle around a center point, all parented
    to a rig controller. Rotate the rig to orbit all cameras around the subject, or
    switch between cameras for instant angle changes.

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
        - cameras: List of dicts with name, angle, focalLength, heightOffset
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
        - Cameras automatically point at center
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

    return await _execute_by_id("vangard-create-camera-rig", {
        "rigName": rig_name,
        "centerPosition": center_position,
        "cameraCount": camera_count,
        "radius": radius,
        "heightVariation": height_variation,
        "focalLengths": focal_lengths,
    })


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
    if not (0.0 <= flicker_amount <= 1.0):
        raise ToolError("flicker_amount must be between 0.0 and 1.0")
    if strobe_interval < 1:
        raise ToolError("strobe_interval must be at least 1 frame")
    if pulse_count < 1:
        raise ToolError("pulse_count must be at least 1")

    return await _execute_by_id("vangard-animate-light", {
        "lightLabel": light_label,
        "movementType": movement_type,
        "startFrame": start_frame,
        "endFrame": end_frame,
        "intensity": intensity,
        "flickerAmount": flicker_amount,
        "strobeInterval": strobe_interval,
        "pulseCount": pulse_count,
    })


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
    if sequence_type not in ("day-to-night", "night-to-dawn", "interrogation", "romantic", "action-tension"):
        raise ToolError(
            f"Invalid sequence_type '{sequence_type}'. "
            "Valid: day-to-night, night-to-dawn, interrogation, romantic, action-tension"
        )
    if start_frame < 0 or end_frame <= start_frame:
        raise ToolError("start_frame must be >= 0 and end_frame must be > start_frame")

    return await _execute_by_id("vangard-create-light-sequence", {
        "sequenceType": sequence_type,
        "subjectLabel": subject_label,
        "startFrame": start_frame,
        "endFrame": end_frame,
        "createLights": create_lights,
    })


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
    It reads scene state (figure positions, existing cameras/lights) and returns
    a step-by-step action plan with recommended tool calls you can execute next.

    Args:
        shot_type: Cinematic shot size — one of:
            "extreme-close-up", "close-up", "medium-close-up", "medium-shot",
            "medium-full", "full-shot", "wide-shot", "extreme-wide",
            "two-shot", "over-shoulder"
        subject_label: Scene node label for the primary subject (figure or prop).
            Used to calculate camera distance and aim point. If omitted, scene
            origin (0, 130, 0) is used as the default eye-level aim point.
        camera_label: Existing camera to use for recommendation context. If provided,
            tool call suggestions reference this camera by name.
        mood: Emotional tone that drives the lighting recommendation — one of:
            "neutral", "dramatic", "happy", "sad", "tense", "romantic",
            "horror", "action"
        composition_rule: Framing principle for horizontal camera offset — one of:
            "rule-of-thirds", "center-frame", "golden-ratio", "leading-lines"

    Returns:
        dict with keys:
        - shotType, shotDescription, mood, compositionRule
        - subject, camera
        - sceneState: {numCameras, numLights, numSkeletons, figures[]}
        - recommendations:
            - camera: {position, focalLength, distanceFromSubject, horizontalAngle,
                       verticalAngle, steps[]}
            - lighting: {preset, keyFlux, fillFlux, rimFlux, keyAngle, notes, steps[]}
            - character: {steps[]}
            - toolSequence: ordered list of suggested tool calls to execute

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
        - Camera position is relative to subject's current world position
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

    return await _execute_by_id("vangard-plan-shot", {
        "shotType": shot_type,
        "subjectLabel": subject_label,
        "cameraLabel": camera_label,
        "mood": mood,
        "compositionRule": composition_rule,
    })


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

    Each shot in the storyboard gets its own camera node in the scene (when
    save_presets=True), positioned and aimed at the subject. The returned
    data includes frame ranges for the full timeline and per-shot details
    ready for rendering or animation.

    Args:
        title: Name for this storyboard (used as camera name prefix).
        shots: List of shot definition dicts. Each dict may contain:
            - shotType (str): One of the standard shot sizes (default "medium-shot").
                Valid: "extreme-close-up", "close-up", "medium-close-up",
                "medium-shot", "medium-full", "full-shot", "wide-shot",
                "extreme-wide", "two-shot", "over-shoulder"
            - label (str): Human-readable shot name (e.g. "Scene 1 - Establishing").
            - subjectLabel (str): Scene node to point camera at.
            - cameraLabel (str): Override camera node name (default: title_Cam1, etc.).
            - durationFrames (int): Shot length in frames (default: frames_per_shot).
            - focalLength (int): Override focal length in mm.
            - distance (int): Override camera-to-subject distance in cm.
            - angle (int): Horizontal camera angle in degrees (0=front, 90=right).
            - description (str): Scene description / visual note.
            - action (str): Character action description.
            - dialogue (str): Spoken dialogue for this shot.
        start_frame: First frame of the storyboard timeline (default 0).
        frames_per_shot: Default frame count when durationFrames is not specified
            per shot (default 90 = 3 seconds at 30fps).
        save_presets: If True (default), create a camera node in the scene for
            each shot. If False, return planning data only without scene changes.

    Returns:
        dict with keys: title, totalShots, totalFrames, totalSeconds,
        startFrame, endFrame, shots[], suggestions[].
        Each shot entry contains: shotNumber, label, shotType, subject, camera,
        cameraCreated, focalLength, distance, angle, startFrame, endFrame,
        durationFrames, durationSeconds, description, action, dialogue.

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
        - If a camera with the same label already exists, it is reused (not recreated)
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

    # Validate shot types
    for i, shot in enumerate(shots):
        st = shot.get("shotType", "medium-shot")
        if st not in _VALID_SHOT_TYPES:
            raise ToolError(
                f"Shot {i + 1} has invalid shotType '{st}'. "
                f"Valid: {', '.join(sorted(_VALID_SHOT_TYPES))}"
            )

    return await _execute_by_id("vangard-create-storyboard", {
        "title": title,
        "shots": shots,
        "startFrame": start_frame,
        "framesPerShot": frames_per_shot,
        "savePresets": save_presets,
    })


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

    Either aims focus at a named scene node (auto-calculating distance) or sets
    an explicit focal distance in centimetres. Optionally enables DOF rendering
    and sets the F/Stop (aperture) for blur amount control.

    Args:
        camera_label: Label of the camera node to configure (e.g. "Camera 1").
        target_label: Scene node to focus on. Distance is auto-calculated from
            the camera to the node. For figures, eye-level (+130 cm) is used as
            the aim point. Mutually exclusive with focal_distance — if both are
            given, target_label takes precedence.
        focal_distance: Explicit focus distance in centimetres from the camera.
            Required if target_label is not provided.
        f_stop: Lens aperture (F/Stop value). Controls depth-of-field blur:
            - 1.4–2.8 → very shallow DOF (cinematic portrait blur)
            - 4–5.6   → moderate blur (standard portrait)
            - 8–11    → deep DOF (landscape / group shots)
            - 16+     → near-infinite focus (everything sharp)
            If None, F/Stop is left unchanged.
        enable_dof: Whether to enable depth-of-field rendering on the camera
            (default True). Set False to only update distance without enabling DOF.

    Returns:
        dict with keys: camera, target, focalDistance, fStop, dofEnabled,
        propertiesSet (details of which properties were found and set),
        dofPreview (estimated near/far blur boundaries), suggestions.

    Examples:
        # Focus on Genesis 9 (auto-distance), cinematic shallow DOF
        result = daz_set_focus_point(
            "Camera 1", target_label="Genesis 9", f_stop=1.8
        )

        # Manual distance — product shot with moderate blur
        result = daz_set_focus_point(
            "Camera 1", focal_distance=150, f_stop=4.0
        )

        # Portrait with narrow aperture (everything sharp)
        result = daz_set_focus_point(
            "Portrait Cam", target_label="Alice", f_stop=11.0
        )

        # Update distance only, keep existing F/Stop and DOF state
        result = daz_set_focus_point(
            "Camera 1", focal_distance=200, enable_dof=False
        )

    Notes:
        - DAZ Studio uses multiple property name conventions across versions;
          this tool tries "Focal Distance", "Focus Distance", "focalDistance"
        - If a property is not found, a note is returned but no error is raised
        - DOF effect is only visible in Iray/3Delight renders, not the viewport
        - Use daz_animate_focus_pull to animate a rack focus between subjects
        - Combine with daz_render or daz_render_animation to render with DOF
    """
    if target_label is None and focal_distance is None:
        raise ToolError("Either target_label or focal_distance must be provided")
    if focal_distance is not None and focal_distance <= 0:
        raise ToolError("focal_distance must be greater than 0")
    if f_stop is not None and (f_stop < 0.7 or f_stop > 64):
        raise ToolError("f_stop must be between 0.7 and 64")

    return await _execute_by_id("vangard-set-focus-point", {
        "cameraLabel": camera_label,
        "targetLabel": target_label,
        "focalDistance": focal_distance,
        "fStop": f_stop,
        "enableDof": enable_dof,
    })


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

    Creates keyframes on the camera's focal distance property to smoothly shift
    focus from one point to another over a frame range. Supports optional hold
    periods at the start and end, letting you hold sharp on subject A, pull to
    subject B, and hold there.

    Args:
        camera_label: Label of the camera node to animate (e.g. "Camera 1").
        from_target: Scene node label to focus at the start of the pull.
            Distance is auto-calculated from camera to node.
        to_target: Scene node label to focus at the end of the pull.
            Distance is auto-calculated from camera to node.
        from_distance: Explicit start focal distance in cm. Used when
            from_target is not provided.
        to_distance: Explicit end focal distance in cm. Used when
            to_target is not provided.
        start_frame: First frame of the animation range (default 0).
        end_frame: Last frame of the animation range (default 60 = 2 sec at 30fps).
        hold_from_frames: Frames to hold focus on from-subject before pulling
            (default 0). Hold period is at the start of the frame range.
        hold_to_frames: Frames to hold focus on to-subject after the pull
            (default 0). Hold period is at the end of the frame range.
        f_stop: Set aperture at the start of the animation. Low values (1.4–2.8)
            produce more pronounced blur separation during the pull.

    Returns:
        dict with keys: camera, fromTarget, fromDistance, toTarget, toDistance,
        fStop, focalDistanceProperty, startFrame, endFrame, pullStartFrame,
        pullEndFrame, keyframes[], pullDurationFrames, pullDurationSeconds,
        suggestions.

    Examples:
        # Classic 2-second rack focus: Alice → Bob
        result = daz_animate_focus_pull(
            camera_label="Camera 1",
            from_target="Alice",
            to_target="Bob",
            start_frame=0, end_frame=59,
            f_stop=2.0
        )

        # Hold on Alice for 1 sec, pull to Bob over 2 sec, hold 1 sec
        result = daz_animate_focus_pull(
            "Camera 1",
            from_target="Alice", to_target="Bob",
            start_frame=0, end_frame=119,
            hold_from_frames=30, hold_to_frames=30,
            f_stop=1.8
        )

        # Manual distances — product close-up pull
        result = daz_animate_focus_pull(
            "Macro Cam",
            from_distance=40, to_distance=20,
            start_frame=0, end_frame=45
        )

    Notes:
        - Requires DOF to be enabled on the camera (use daz_set_focus_point first,
          or this tool will attempt to enable it automatically)
        - Camera must have a "Focal Distance" property — enable DOF in DAZ Studio
          camera parameters before calling if the tool reports property not found
        - Frame layout: [start] --hold-from-- [pull-start] → [pull-end] --hold-to-- [end]
        - Use low F/Stop (1.4–2.8) to maximise the visual impact of the focus pull
        - Combine with daz_render_animation to export the animated sequence
    """
    if from_target is None and from_distance is None:
        raise ToolError("Either from_target or from_distance must be provided")
    if to_target is None and to_distance is None:
        raise ToolError("Either to_target or to_distance must be provided")
    if start_frame < 0 or end_frame <= start_frame:
        raise ToolError("start_frame must be >= 0 and end_frame must be > start_frame")
    if hold_from_frames < 0 or hold_to_frames < 0:
        raise ToolError("hold_from_frames and hold_to_frames must be >= 0")
    if from_distance is not None and from_distance <= 0:
        raise ToolError("from_distance must be greater than 0")
    if to_distance is not None and to_distance <= 0:
        raise ToolError("to_distance must be greater than 0")
    if f_stop is not None and (f_stop < 0.7 or f_stop > 64):
        raise ToolError("f_stop must be between 0.7 and 64")

    return await _execute_by_id("vangard-animate-focus-pull", {
        "cameraLabel": camera_label,
        "fromTarget": from_target,
        "toTarget": to_target,
        "fromDistance": from_distance,
        "toDistance": to_distance,
        "startFrame": start_frame,
        "endFrame": end_frame,
        "holdFromFrames": hold_from_frames,
        "holdToFrames": hold_to_frames,
        "fStop": f_stop,
    })


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

    Controls the Environment node (found via `Scene.findNodeByLabel("Environment Options")`)
    which governs the
    HDRI dome, Sun-Sky system, and ambient lighting. Call with only the parameters
    you want to change — others are left untouched.

    Args:
        environment_mode: Sets the overall lighting environment:
            - 0 = Sun-Sky Only  (outdoor sky, no HDRI dome)
            - 1 = Dome Only     (HDRI dome image, no sun-sky)
            - 2 = Sun-Sky + Dome (combined)
            - 3 = Scene Only    (use only scene lights — disables dome/sun entirely)
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
        - The Environment node is located via Scene.findNodeByLabel("Environment Options")
        - Property names vary across DAZ Studio versions; the tool tries multiple names
        - Mode 3 is automatically set by daz_apply_lighting_preset and daz_apply_visual_style
        - Changes are immediate but only visible in rendered output (not realtime viewport)
    """
    if environment_mode is not None and environment_mode not in _VALID_ENV_MODES:
        raise ToolError(
            f"Invalid environment_mode {environment_mode}. "
            "Valid: 0 (Sun-Sky Only), 1 (Dome Only), 2 (Sun-Sky+Dome), 3 (Scene Only)"
        )
    if environment_intensity is not None and not (0.0 <= environment_intensity <= 10.0):
        raise ToolError("environment_intensity must be between 0.0 and 10.0")
    if dome_scale is not None and not (0.01 <= dome_scale <= 100.0):
        raise ToolError("dome_scale must be between 0.01 and 100.0")
    if dome_rotation is not None and not (0.0 <= dome_rotation <= 360.0):
        raise ToolError("dome_rotation must be between 0.0 and 360.0")
    if sun_light_intensity is not None and not (0.0 <= sun_light_intensity <= 10.0):
        raise ToolError("sun_light_intensity must be between 0.0 and 10.0")

    return await _execute_by_id("vangard-set-scene-atmosphere", {
        "environmentMode": environment_mode,
        "environmentIntensity": environment_intensity,
        "drawDome": draw_dome,
        "domeScale": dome_scale,
        "domeRotation": dome_rotation,
        "sunLightIntensity": sun_light_intensity,
    })


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
    if not (0.1 <= intensity <= 5.0):
        raise ToolError("intensity must be between 0.1 and 5.0")

    return await _execute_by_id("vangard-apply-visual-style", {
        "styleName": style_name,
        "subjectLabel": subject_label,
        "intensity": intensity,
    })


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
    result = await _execute_by_id("vangard-read-node-config", {
        "nodeLabels": node_labels or [],
        "includeTypes": include_types,
    })

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
    if not (0.0001 <= scale_transforms <= 1000.0):
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
    result = await _execute_by_id("vangard-write-node-config", {
        "config": config,
        "skipMissing": skip_missing,
        "scaleTransforms": scale_transforms,
    })

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
    if not (0.0 <= intensity <= 1.0):
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

    definition = _EMOTION_DEFINITIONS[emotion]
    return await _execute_by_id("vangard-time-expression", {
        "nodeLabel":        character_label,
        "morphList":        definition["morphs"],
        "bodyAdjustments":  definition["body"],
        "intensity":        intensity,
        "easeInStart":      ease_in_start,
        "holdStart":        hold_start,
        "holdEnd":          hold_end,
        "easeOutEnd":       ease_out_end if ease_out_frames > 0 else hold_end,
        "baselineFrame":    baseline_frame,
    })


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

        definition = _EMOTION_DEFINITIONS[emotion]
        try:
            char_result = await _execute_by_id("vangard-time-expression", {
                "nodeLabel":       label,
                "morphList":       definition["morphs"],
                "bodyAdjustments": definition["body"],
                "intensity":       char_intensity,
                "easeInStart":     ease_in_start,
                "holdStart":       hold_start,
                "holdEnd":         hold_end,
                "easeOutEnd":      ease_out_end if char_ease_out > 0 else hold_end,
                "baselineFrame":   None,
            })
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
