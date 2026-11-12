"""Camera and lighting tools for the Vangard DAZ MCP server."""
from __future__ import annotations

import json
from typing import Any

from fastmcp.exceptions import ToolError

from .._mcp import mcp, _execute_by_id, _execute


# ---------------------------------------------------------------------------
# Mood / time-of-day presets (used by new inline-script tools)
# ---------------------------------------------------------------------------

MOOD_PRESETS: dict[str, dict[str, Any]] = {
    "romantic":     {"intensity": 0.6,  "color": [255, 200, 150]},  # warm, soft
    "dramatic":     {"intensity": 1.5,  "color": [200, 200, 220]},  # high contrast, blue-white
    "scary":        {"intensity": 0.4,  "color": [100, 130, 180]},  # cold, dim
    "golden-hour":  {"intensity": 1.2,  "color": [255, 200, 100]},  # golden warm
    "mysterious":   {"intensity": 0.5,  "color": [150, 150, 200]},  # cool blue
    "peaceful":     {"intensity": 0.8,  "color": [255, 220, 180]},  # soft warm
}

TIME_OF_DAY_PRESETS: dict[str, dict[str, Any]] = {
    "dawn":         {"intensity": 0.5,  "color": [255, 180, 120]},
    "morning":      {"intensity": 0.8,  "color": [255, 220, 180]},
    "noon":         {"intensity": 1.5,  "color": [255, 255, 240]},
    "golden-hour":  {"intensity": 1.2,  "color": [255, 200, 100]},
    "dusk":         {"intensity": 0.6,  "color": [200, 120, 100]},
    "night":        {"intensity": 0.15, "color": [60,  60,  120]},
}


# ---------------------------------------------------------------------------
# Camera tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_set_active_camera(camera_label: str) -> dict[str, Any]:
    """Set which camera is active in the DAZ Studio viewport.

    Changes the active viewport camera to show the scene from the specified
    camera's perspective. The previous active camera is returned for reference.

    Args:
        camera_label: Display label of the camera to activate.

    Returns:
      - success: true on success
      - camera: label of the camera that was activated
      - previousCamera: label of the previously active camera (or null)

    Example:
        # Switch to a specific camera
        daz_set_active_camera("Camera 1")

        # Switch to a custom camera
        daz_set_active_camera("Close Up Camera")

        # Switch back to default camera
        daz_set_active_camera("Perspective View")

    Note:
        The camera must exist in the scene. Use daz_scene_info() to list
        available cameras. The viewport updates immediately to show the
        camera's current view.
    """
    return await _execute_by_id("vangard-set-active-camera", {"cameraLabel": camera_label})


@mcp.tool()
async def daz_orbit_camera_around(
    camera_label: str,
    target_label: str,
    distance: float = 200.0,
    angle_horizontal: float = 45.0,
    angle_vertical: float = 15.0,
) -> dict[str, Any]:
    """Position camera orbiting around a target node at specified angle and distance.

    Uses spherical coordinates to position the camera at a specific angle around
    a target object. The camera is automatically aimed at the target after positioning.

    Args:
        camera_label: Display label of the camera to position.
        target_label: Display label of the target node to orbit around.
        distance: Distance from target in centimeters (default: 200).
        angle_horizontal: Horizontal angle in degrees, 0=front/+Z, 90=right/+X (default: 45).
        angle_vertical: Vertical angle in degrees, positive=above, negative=below (default: 15).

    Returns:
      - success: true on success
      - camera: camera label
      - target: target node label
      - position: camera world position {x, y, z}
      - targetPosition: target world position {x, y, z}

    Example:
        # Position camera at 45° to the right, slightly above, 200cm away
        daz_orbit_camera_around("Camera 1", "Genesis 9", distance=200,
                                angle_horizontal=45, angle_vertical=15)

        # Side view from the left
        daz_orbit_camera_around("Camera 1", "Genesis 9", distance=150,
                                angle_horizontal=-90, angle_vertical=0)

        # Bird's eye view
        daz_orbit_camera_around("Camera 1", "Genesis 9", distance=300,
                                angle_horizontal=0, angle_vertical=60)

        # Dramatic low angle
        daz_orbit_camera_around("Camera 1", "Genesis 9", distance=180,
                                angle_horizontal=25, angle_vertical=-20)

    Note:
        Angles use spherical coordinates:
        - Horizontal: 0°=front(+Z), 90°=right(+X), 180°=back(-Z), -90°=left(-X)
        - Vertical: positive=above horizon, negative=below

        Camera is automatically aimed at the target's world position after positioning.
    """
    return await _execute_by_id(
        "vangard-orbit-camera-around",
        {
            "cameraLabel": camera_label,
            "targetLabel": target_label,
            "distance": distance,
            "angleHorizontal": angle_horizontal,
            "angleVertical": angle_vertical,
        },
    )


@mcp.tool()
async def daz_frame_camera_to_node(
    camera_label: str,
    node_label: str,
    distance: float | None = None,
) -> dict[str, Any]:
    """Frame camera to show a node by positioning at calculated distance.

    Positions the camera to frame the specified node in view. Calculates the
    node's bounding box and positions the camera at an appropriate distance
    to show the entire object. Camera is positioned in front (+Z) and aimed
    at the node's center.

    Args:
        camera_label: Display label of the camera to position.
        node_label: Display label of the node to frame.
        distance: Optional distance from node center in cm. If not specified,
                  calculated as 2.5x the largest dimension of the node's bounding box.

    Returns:
      - success: true on success
      - camera: camera label
      - node: node label
      - position: camera world position {x, y, z}
      - nodeCenter: node bounding box center {x, y, z}
      - nodeSize: node bounding box size {x, y, z}

    Example:
        # Frame a character (auto distance)
        daz_frame_camera_to_node("Camera 1", "Genesis 9")

        # Frame a prop with specific distance
        daz_frame_camera_to_node("Camera 1", "Sword", distance=50)

        # Frame entire scene
        daz_frame_camera_to_node("Camera 1", "Scene", distance=500)

        # Close-up on head
        daz_frame_camera_to_node("Camera 1", "head", distance=30)

    Note:
        - Auto-calculated distance is 2.5x the largest bounding box dimension
        - Camera is positioned in front of the node (+Z direction)
        - Camera is aimed at the center of the node's bounding box
        - Useful for automatically framing objects of varying sizes
    """
    args: dict[str, Any] = {
        "cameraLabel": camera_label,
        "nodeLabel": node_label,
    }
    if distance is not None:
        args["distance"] = distance

    return await _execute_by_id("vangard-frame-camera-to-node", args)


@mcp.tool()
async def daz_save_camera_preset(camera_label: str) -> dict[str, Any]:
    """Save camera position and rotation as preset data.

    Captures the current transform properties of a camera (position, rotation,
    scale) and returns them as preset data. This data can be saved by the client
    and later restored using daz_load_camera_preset().

    Args:
        camera_label: Display label of the camera to save.

    Returns:
      - preset: Dictionary containing:
        - label: camera label
        - transforms: Dictionary of property names to values (XTranslate, YTranslate,
                     ZTranslate, XRotate, YRotate, ZRotate, XScale, YScale, ZScale)

    Example:
        # Save camera position
        preset = daz_save_camera_preset("Camera 1")

        # Client can store preset data (e.g., in a file or database)
        import json
        with open("my_camera_preset.json", "w") as f:
            json.dump(preset, f)

        # Later, restore the camera
        with open("my_camera_preset.json") as f:
            preset = json.load(f)
        daz_load_camera_preset("Camera 1", preset["preset"])

    Note:
        - Preset data is a plain dictionary that can be serialized (JSON, etc.)
        - Includes all transform properties (position, rotation, scale)
        - Does not include camera-specific settings (focal length, DOF, etc.)
        - Preset data can be applied to any camera, not just the original
    """
    return await _execute_by_id("vangard-save-camera-preset", {"cameraLabel": camera_label})


@mcp.tool()
async def daz_load_camera_preset(camera_label: str, preset: dict[str, Any]) -> dict[str, Any]:
    """Restore camera position and rotation from preset data.

    Applies saved preset data (from daz_save_camera_preset()) to a camera,
    restoring its position, rotation, and scale.

    Args:
        camera_label: Display label of the camera to modify.
        preset: Preset dictionary from daz_save_camera_preset(), containing:
                - transforms: Dictionary of property names to values

    Returns:
      - success: true on success
      - camera: camera label
      - applied: list of property names that were applied

    Example:
        # Load previously saved preset
        with open("my_camera_preset.json") as f:
            preset = json.load(f)

        result = daz_load_camera_preset("Camera 1", preset["preset"])
        print(f"Applied properties: {result['applied']}")

        # Apply same preset to multiple cameras
        cameras = ["Camera 1", "Camera 2", "Camera 3"]
        for cam in cameras:
            daz_load_camera_preset(cam, preset["preset"])

    Note:
        - Preset can be applied to any camera, not just the original
        - Only properties present in the preset are modified
        - Useful for saving/loading camera positions across sessions
        - Can be used to synchronize multiple cameras
    """
    return await _execute_by_id(
        "vangard-load-camera-preset",
        {"cameraLabel": camera_label, "preset": preset},
    )


# ---------------------------------------------------------------------------
# Lighting preset / composition tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_apply_lighting_preset(
    preset: str,
    subject_label: str | None = None,
) -> dict[str, Any]:
    """Create a professional photography lighting setup in one command.

    Removes any existing lights with the same names, creates new lights
    at positions calculated relative to the subject's bounding box,
    aims each light at the subject's face height, and sets the environment
    to scene-lights-only mode (disables the dome).

    Available presets:
        three-point  - Key (front-right) + Fill (front-left) + Rim (back).
                       The most versatile general-purpose lighting setup.
        rembrandt    - Key (45° side, high) + dim Fill. Creates triangle of
                       light under opposite eye. Dramatic portrait lighting.
        butterfly    - Key directly in front, high. Glamour/beauty lighting.
                       Creates butterfly shadow under the nose.
        split        - Key directly to one side (90°). Half face lit, half in
                       shadow. Moody, high-contrast.
        loop         - Key (35° side) + Fill + Rim. Natural-looking portrait.
                       Small loop shadow on opposite cheek.

    Args:
        preset: Lighting preset name (see above)
        subject_label: Optional node label to anchor lights around. If omitted,
                       lights are placed relative to scene origin at 170cm height.

    Returns:
        {
            "preset": "three-point",
            "subject": "Genesis 9",
            "lights_created": [
                {"label": "Key Light", "type": "DzSpotLight",
                 "position": {"x": 150, "y": 180, "z": 150}, "flux": 2000}
            ],
            "environment_mode": "Scene Only (3)"
        }
    """
    args: dict[str, Any] = {"preset": preset}
    if subject_label is not None:
        args["subjectLabel"] = subject_label
    return await _execute_by_id("vangard-apply-lighting-preset", args)


@mcp.tool()
async def daz_apply_composition_rule(
    camera_label: str,
    subject_label: str,
    rule: str = "rule-of-thirds",
) -> dict[str, Any]:
    """Position camera so subject is framed according to a photography composition rule.

    The camera maintains approximately its current horizontal distance from the subject
    while adjusting position and aim to satisfy the chosen rule.

    Args:
        camera_label: Node label of the camera to reposition.
        subject_label: Node label of the subject to frame.
        rule: One of:
            - "rule-of-thirds"  — Subject on right vertical third at eye level (default)
            - "golden-ratio"    — Subject at the golden section (1.618 proportion)
            - "center-frame"    — Subject centred, symmetric framing
            - "leading-lines"   — Low angle with diagonal offset toward subject

    Returns:
        Dict with camera, subject, rule, camera_position, and explanation string.
    """
    return await _execute_by_id("vangard-apply-composition-rule", {
        "cameraLabel": camera_label,
        "subjectLabel": subject_label,
        "rule": rule,
    })


@mcp.tool()
async def daz_frame_shot(
    camera_label: str,
    subject_label: str,
    shot_type: str = "medium-shot",
) -> dict[str, Any]:
    """Frame camera to subject using a standard cinematic shot type.

    Calculates camera distance and height from the subject's bounding box,
    then positions and aims the camera accordingly. Genesis figures face +Z,
    so the camera is placed in front (positive Z direction).

    Args:
        camera_label: Node label of the camera to reposition.
        subject_label: Node label of the subject to frame.
        shot_type: One of:
            - "extreme-close-up"  — Eyes/mouth detail (~25 cm)
            - "close-up"          — Face and head (~50 cm)
            - "medium-close-up"   — Head and shoulders (~90 cm)
            - "medium-shot"       — Waist up (~140 cm)
            - "medium-full"       — Knees up (~200 cm)
            - "full-shot"         — Entire body (~400 cm)
            - "wide-shot"         — Body within environment (~700 cm)

    Returns:
        Dict with camera, subject, shot_type, distance, camera_height, and framing description.
    """
    return await _execute_by_id("vangard-frame-shot", {
        "cameraLabel": camera_label,
        "subjectLabel": subject_label,
        "shotType": shot_type,
    })


@mcp.tool()
async def daz_apply_camera_angle(
    camera_label: str,
    subject_label: str,
    angle: str = "eye-level",
) -> dict[str, Any]:
    """Apply a standard camera angle preset relative to a subject.

    Maintains the camera's current horizontal distance from the subject while
    adjusting vertical position and aim to achieve the specified angle. If the
    camera is closer than 50 cm it defaults to 250 cm.

    Args:
        camera_label: Node label of the camera to reposition.
        subject_label: Node label of the subject.
        angle: One of:
            - "eye-level"      — Camera at subject's eye height (neutral, default)
            - "high-angle"     — Camera above subject (~1.5× head height), looking down
            - "low-angle"      — Camera at shin level, looking up (powerful/dominant)
            - "dutch-angle"    — Eye level with 15° Z-roll (unsettling, tense)
            - "overhead"       — Camera directly above (bird's-eye view)
            - "worms-eye"      — Camera at ground level looking straight up
            - "over-shoulder"  — Camera behind and to one side of subject

    Returns:
        Dict with camera, subject, angle, camera_position, and descriptive note.
    """
    return await _execute_by_id("vangard-apply-camera-angle", {
        "cameraLabel": camera_label,
        "subjectLabel": subject_label,
        "angle": angle,
    })


# ---------------------------------------------------------------------------
# Light listing / creation (dazpy-migrated + registered script)
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_list_lights() -> dict[str, Any]:
    """List all lights currently in the scene.

    Returns position, type, and flux (intensity) for every light node. Use the
    returned ``label`` values with ``daz_set_property``, ``daz_delete_node``,
    or ``daz_animate_light``.

    Returns:
        Dict with:
        - light_count: number of lights
        - lights: list of {index, label, name, type, position, flux, enabled}

    Examples:
        daz_list_lights()
        # → {"light_count": 3, "lights": [{"label": "Key Light", ...}]}

    Notes:
        - ``type`` is the DazScript class name (e.g. "DzSpotLight", "DzDistantLight").
        - ``flux`` is in DAZ Studio's internal units (roughly equivalent to
          Watts for Iray); ``null`` if the light has no Flux property.
    """
    return await _execute_by_id("vangard-list-lights")


@mcp.tool()
async def daz_create_light(
    light_type: str,
    label: str,
    x: float = 0.0,
    y: float = 200.0,
    z: float = 200.0,
    flux: float | None = None,
    aim_at_label: str | None = None,
) -> dict[str, Any]:
    """Create a new light and add it to the scene.

    Creates the light at the given world-space position (in centimetres) and
    optionally aims it at a scene node's bounding-box centre.

    Args:
        light_type: One of ``"spot"`` (default), ``"distant"``, or ``"point"``.
        label: Display name to assign to the new light.
        x: World-space X position in cm (default 0).
        y: World-space Y position in cm (default 200).
        z: World-space Z position in cm (default 200).
        flux: Light intensity in DAZ flux units. If omitted, DAZ default is used.
        aim_at_label: If provided, aim the light at this node's centre.

    Returns:
        Dict with label, type, position, and flux.

    Examples:
        daz_create_light("spot", "Key Light", x=150, y=250, z=200, flux=10000,
                         aim_at_label="Genesis 9")
        daz_create_light("distant", "Sun", x=0, y=500, z=0, flux=5000)
        daz_create_light("point", "Candle", x=0, y=80, z=50, flux=2000)

    Notes:
        - For complex multi-light setups prefer daz_apply_lighting_preset.
        - Use daz_list_lights to verify the light was added.
    """
    valid_types = ("spot", "distant", "point")
    if light_type not in valid_types:
        raise ToolError(
            f"light_type must be one of {valid_types}, got '{light_type}'"
        )
    return await _execute_by_id(
        "vangard-create-light",
        {
            "lightType": light_type,
            "label": label,
            "x": x,
            "y": y,
            "z": z,
            "flux": flux,
            "aimAtLabel": aim_at_label,
        },
    )


# ---------------------------------------------------------------------------
# Camera listing / creation
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_list_cameras() -> dict[str, Any]:
    """List all cameras currently in the scene.

    Returns position and focal length for every camera node. Use the returned
    ``label`` values with ``daz_set_active_camera``, ``daz_render_with_camera``,
    or ``daz_delete_node``.

    Returns:
        Dict with:
        - camera_count: number of cameras
        - cameras: list of {index, label, name, type, position, focal_length}

    Examples:
        daz_list_cameras()
        # → {"camera_count": 2, "cameras": [{"label": "Camera 1", ...}]}
    """
    return await _execute_by_id("vangard-list-cameras")


@mcp.tool()
async def daz_create_camera(
    label: str,
    x: float = 0.0,
    y: float = 150.0,
    z: float = 300.0,
    aim_at_label: str | None = None,
    focal_length: float | None = None,
) -> dict[str, Any]:
    """Create a new camera and add it to the scene.

    Creates a basic camera at the given world-space position (in centimetres) and
    optionally aims it at a scene node's bounding-box centre.

    Args:
        label: Display name to assign to the new camera.
        x: World-space X position in cm (default 0).
        y: World-space Y position in cm (default 150).
        z: World-space Z position in cm (default 300).
        aim_at_label: If provided, aim the camera at this node's centre.
        focal_length: Lens focal length in mm. If omitted, DAZ default is used.

    Returns:
        Dict with label, position, and focal_length.

    Examples:
        daz_create_camera("Close-up Cam", x=0, y=160, z=120,
                          aim_at_label="Genesis 9", focal_length=85)
        daz_create_camera("Wide Shot", x=-200, y=180, z=350,
                          aim_at_label="Genesis 9")

    Notes:
        - Use daz_set_active_camera to switch the active viewport camera.
        - Use daz_list_cameras to confirm the camera was added.
    """
    return await _execute_by_id(
        "vangard-create-camera",
        {
            "label": label,
            "x": x,
            "y": y,
            "z": z,
            "aimAtLabel": aim_at_label,
            "focalLength": focal_length,
        },
    )


# ---------------------------------------------------------------------------
# New tools: mood / time-of-day lighting via inline DazScript
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_set_mood_lighting(
    mood: str,
    figure_label: str | None = None,  # pylint: disable=unused-argument
    # Reserved for future per-figure filtering; see docstring below.
) -> dict[str, Any]:
    """Apply a mood-based lighting colour and intensity adjustment to all scene lights.

    Iterates every light in the scene and sets its intensity and diffuse colour
    to match the requested mood.  Optionally focuses the adjustment on lights
    that aim at a particular figure (by name).

    Available moods:
        romantic     - Warm, soft (intensity 0.6, warm orange)
        dramatic     - High contrast, blue-white (intensity 1.5)
        scary        - Cold and dim (intensity 0.4, steel blue)
        golden-hour  - Rich golden warm (intensity 1.2)
        mysterious   - Cool blue, mid-dim (intensity 0.5)
        peaceful     - Soft warm (intensity 0.8)

    Args:
        mood: One of the mood names listed above.
        figure_label: Optional figure label to aim-check. Currently unused by the
                      DazScript; reserved for future per-figure filtering.

    Returns:
        {
            "mood": "romantic",
            "lights_adjusted": 3,
            "intensity": 0.6,
            "color": [255, 200, 150]
        }
    """
    if mood not in MOOD_PRESETS:
        valid = ", ".join(f'"{k}"' for k in MOOD_PRESETS)
        raise ToolError(f"Unknown mood '{mood}'. Valid moods: {valid}")

    preset = MOOD_PRESETS[mood]
    intensity = preset["intensity"]
    r, g, b = preset["color"]

    script = f"""
(function() {{
    var count = 0;
    var numLights = Scene.getNumLights();
    for (var i = 0; i < numLights; i++) {{
        var light = Scene.getLight(i);
        var ip = light.findPropertyByLabel('Intensity');
        if (ip) {{ ip.setValue({intensity}); }}
        var cp = light.findPropertyByLabel('Diffuse Color');
        if (cp) {{ cp.setValue(new Color({r}, {g}, {b})); }}
        count++;
    }}
    return {{ mood: {json.dumps(mood)}, lights_adjusted: count,
              intensity: {intensity}, color: [{r}, {g}, {b}] }};
}})()
"""
    return await _execute(script)


@mcp.tool()
async def daz_apply_time_of_day(
    time_of_day: str,
    figure_label: str | None = None,  # pylint: disable=unused-argument
    # Reserved for future per-figure filtering; see docstring below.
) -> dict[str, Any]:
    """Adjust all scene lights to simulate a particular time of day.

    Sets light intensity and colour temperature across all scene lights to
    approximate the natural lighting quality for the chosen time.

    Available times:
        dawn         - Soft orange-pink (intensity 0.5)
        morning      - Warm soft daylight (intensity 0.8)
        noon         - Bright near-white (intensity 1.5)
        golden-hour  - Rich golden warm (intensity 1.2)
        dusk         - Deep red-orange (intensity 0.6)
        night        - Very dim cool blue (intensity 0.15)

    Args:
        time_of_day: One of the time names listed above.
        figure_label: Optional figure label. Reserved for future per-figure
                      filtering; currently applies to all scene lights.

    Returns:
        {
            "time_of_day": "golden-hour",
            "lights_adjusted": 3,
            "intensity": 1.2,
            "color": [255, 200, 100]
        }
    """
    if time_of_day not in TIME_OF_DAY_PRESETS:
        valid = ", ".join(f'"{k}"' for k in TIME_OF_DAY_PRESETS)
        raise ToolError(f"Unknown time_of_day '{time_of_day}'. Valid values: {valid}")

    preset = TIME_OF_DAY_PRESETS[time_of_day]
    intensity = preset["intensity"]
    r, g, b = preset["color"]

    script = f"""
(function() {{
    var count = 0;
    var numLights = Scene.getNumLights();
    for (var i = 0; i < numLights; i++) {{
        var light = Scene.getLight(i);
        var ip = light.findPropertyByLabel('Intensity');
        if (ip) {{ ip.setValue({intensity}); }}
        var cp = light.findPropertyByLabel('Diffuse Color');
        if (cp) {{ cp.setValue(new Color({r}, {g}, {b})); }}
        count++;
    }}
    return {{ time_of_day: {json.dumps(time_of_day)}, lights_adjusted: count,
              intensity: {intensity}, color: [{r}, {g}, {b}] }};
}})()
"""
    return await _execute(script)
